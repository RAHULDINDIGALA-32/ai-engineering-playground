from __future__ import annotations
 
import argparse
import concurrent.futures
import importlib
import json
import logging
import os
import re
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rag_iter_4 import rag_pipeline as rag

# --------------------------------------------------------------------------- 
# Logging
# --------------------------------------------------------------------------- 
logger = logging.getLogger("rag_evals")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
    )
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


DEFAULT_MIN_RECALL = 0.85
DEFAULT_MIN_PRECISION = 0.0  # informational by default; set >0 to gate on it
DEFAULT_MIN_COMPLETENESS = 0.75
DEFAULT_MIN_PASS_RATE = 0.85
DEFAULT_MAX_FORBIDDEN_VIOLATION_RATE = 0.0  # zero tolerance by default



# =============================================================================
# Data model
# =============================================================================
@dataclass
class RetrievalScore:
    recall_at_k: Optional[float]
    precision_at_k: Optional[float]
    reciprocal_rank: Optional[float]
    retrieved_ids: list[str]
    expected_ids: list[str]
 
 
@dataclass
class GenerationScore:
    refusal_expected: bool
    refusal_correct: Optional[bool]  # None if not applicable to judge cleanly
    faithful: Optional[bool]
    completeness: Optional[float]
    missing_facts: list[str]
    forbidden_violated: Optional[bool]
    judge_notes: str
    judge_error: Optional[str] = None
 
 
@dataclass
class CaseResult:
    test_id: str
    query: str
    category_type: str
    difficulty: str
    answer: str
    retrieval: RetrievalScore
    generation: GenerationScore
    passed: bool
    fail_reasons: list[str]
    latency_s: float
    error: Optional[str] = None
 

# =============================================================================
# Dataset loading & validation
# =============================================================================
def load_golden_dataset(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
 
    cases = data.get("cases", [])
    if not cases:
        raise ValueError(f"No 'cases' found in golden dataset: {path}")
 
    required_fields = {"test_id", "query", "category_type", "refusal_expected"}
    for case in cases:
        missing = required_fields - case.keys()
        if missing:
            raise ValueError(
                f"Case {case.get('test_id', '<unknown>')} is missing "
                f"required fields: {missing}"
            )
 
    logger.info("Loaded %d golden cases from %s", len(cases), path)
    return cases
 
 
def verify_collection_ready() -> None:
    """Fail fast with a clear message rather than 45x confusing empty-result runs."""
    collection_name = getattr(rag, "COLLECTION_NAME", None)
    if collection_name is None or not hasattr(rag, "qdrant_client"):
        return
    try:
        exists = rag.qdrant_client.collection_exists(collection_name)
        if not exists:
            raise RuntimeError(
                f"Qdrant collection '{collection_name}' does not exist. "
                f"Run with --ingest first."
            )
        count = rag.qdrant_client.count(collection_name).count
        if count == 0:
            raise RuntimeError(
                f"Qdrant collection '{collection_name}' is empty. "
                f"Run with --ingest first."
            )
        logger.info("Collection '%s' ready: %d points", collection_name, count)
    except RuntimeError:
        raise
    except Exception as exc: 
        logger.warning("Could not verify collection readiness: %s", exc)
 
 
def run_ingest() -> None:
    for attr in ("load_knowledge_base", "create_collection", "create_payload_indexes",
                 "ingest_knowledge_base"):
        if not hasattr(rag, attr):
            raise AttributeError(
                f"--ingest requires '{attr}' on the RAG module but it was not found."
            )
    logger.info("Ingesting knowledge base into Qdrant ...")
    documents = rag.load_knowledge_base()
    rag.create_collection(recreate=True)
    rag.create_payload_indexes()
    rag.ingest_knowledge_base(documents)
    logger.info("Ingestion complete.")
 


# =============================================================================
# Retrieval scoring
# =============================================================================
def compute_retrieval_metrics(
    retrieved_ids: list[str],
    expected_ids: list[str],
    expected_top1_id: Optional[str],
    k: int,
) -> RetrievalScore:
    """
    Recall@k / Precision@k / MRR over policy IDs.
 
    For cases with no expected relevant policies (negative_out_of_scope,
    most adversarial_injection cases), retrieval metrics are not meaningful
    in the recall/precision sense -- correctness there is scored purely on
    generation (did it refuse correctly?). We report None rather than a
    misleading 0.0 or 1.0.
    """
    retrieved_top_k = retrieved_ids[:k]
 
    if not expected_ids:
        return RetrievalScore(
            recall_at_k=None,
            precision_at_k=None,
            reciprocal_rank=None,
            retrieved_ids=retrieved_top_k,
            expected_ids=expected_ids,
        )
 
    retrieved_set = set(retrieved_top_k)
    expected_set = set(expected_ids)
    hits = retrieved_set & expected_set
 
    recall = len(hits) / len(expected_set)
    precision = (len(hits) / len(retrieved_set)) if retrieved_set else 0.0
 
    reciprocal_rank = None
    if expected_top1_id:
        reciprocal_rank = 0.0
        for rank, rid in enumerate(retrieved_top_k, start=1):
            if rid == expected_top1_id:
                reciprocal_rank = 1.0 / rank
                break
 
    return RetrievalScore(
        recall_at_k=recall,
        precision_at_k=precision,
        reciprocal_rank=reciprocal_rank,
        retrieved_ids=retrieved_top_k,
        expected_ids=expected_ids,
    )


#==============================================================================
# Case execution
# =============================================================================
def run_case(case: dict, top_k: int, judge_model: str) -> CaseResult:
    test_id = case["test_id"]
    query = case["query"]
    category_type = case["category_type"]
    difficulty = case.get("difficulty", "unknown")
    expected_ids = case.get("expected_relevant_policy_ids", [])
    expected_top1_id = case.get("expected_top1_policy_id")
    required_facts = case.get("required_facts", [])
    forbidden_content = case.get("forbidden_content", [])
    refusal_expected = bool(case.get("refusal_expected", False))
 
    start = time.monotonic()
    fail_reasons: list[str] = []
 
    try:
        # --- Retrieval ---------------------------------------------------- #
        results = rag.search_db(query=query, top_k=top_k, is_active=True)
        retrieved_ids = [r.payload.get("id") for r in results]
        retrieval = compute_retrieval_metrics(
            retrieved_ids, expected_ids, expected_top1_id, top_k
        )
 
        return CaseResult(
            test_id=test_id,
            query=query,
            category_type=category_type,
            difficulty=difficulty,
            retrieval=retrieval,
            fail_reasons=fail_reasons,
            latency_s=time.monotonic() - start,
        )
 
    except Exception as exc:  
        logger.exception("Case %s raised an exception", test_id)
        return CaseResult(
            test_id=test_id,
            query=query,
            category_type=category_type,
            difficulty=difficulty,
            answer="",
            retrieval=RetrievalScore(None, None, None, [], expected_ids),
            generation=GenerationScore(
                refusal_expected=refusal_expected,
                refusal_correct=None,
                faithful=None,
                completeness=None,
                missing_facts=[],
                forbidden_violated=None,
                judge_notes="",
                judge_error=None,
            ),
            passed=False,
            fail_reasons=[f"pipeline error: {exc}"],
            latency_s=time.monotonic() - start,
            error=str(exc),
        )
 

# =============================================================================
# Aggregation & reporting
# =============================================================================
def _safe_mean(values: list[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return statistics.mean(vals) if vals else None
 
 
def aggregate(results: list[CaseResult]) -> dict[str, Any]:
    by_category: dict[str, list[CaseResult]] = {}
    for r in results:
        by_category.setdefault(r.category_type, []).append(r)
 
    def summarize(subset: list[CaseResult]) -> dict[str, Any]:
        return {
            "n_cases": len(subset),
            "pass_rate": _safe_mean([1.0 if r.passed else 0.0 for r in subset]),
            "recall_at_k": _safe_mean([r.retrieval.recall_at_k for r in subset]),
            "precision_at_k": _safe_mean([r.retrieval.precision_at_k for r in subset]),
            "mrr": _safe_mean([r.retrieval.reciprocal_rank for r in subset]),
            "n_errors": sum(1 for r in subset if r.error),
        }
 
    return {
        "overall": summarize(results),
        "by_category_type": {cat: summarize(rs) for cat, rs in sorted(by_category.items())},
    }
 
 
def _fmt(x: Optional[float], pct: bool = True) -> str:
    if x is None:
        return "  n/a"
    return f"{x * 100:5.1f}%" if pct else f"{x:5.2f}"
 
 
def print_report(results: list[CaseResult], agg: dict[str, Any], top_k: int) -> None:
    print("\n" + "=" * 100)
    print("RAG EVALUATION REPORT")
    print("=" * 100)
    print(f"Cases run: {len(results)}   |   top_k: {top_k}   |   "
          f"generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z")
 
    header = (
        f"{'category_type':<24}{'n':>4}{'pass%':>8}{'recall':>9}{'prec':>8}"
        f"{'mrr':>7}{'faith%':>9}{'complete':>10}{'forbid%':>9}{'refuse%':>9}"
    )
    print("\n" + header)
    print("-" * len(header))
    for cat, s in agg["by_category_type"].items():
        print(
            f"{cat:<24}{s['n_cases']:>4}{_fmt(s['pass_rate']):>8}"
            f"{_fmt(s['recall_at_k']):>9}{_fmt(s['precision_at_k']):>8}"
            f"{_fmt(s['mrr'], pct=False):>7}{_fmt(s['faithfulness_rate']):>9}"
            f"{_fmt(s['completeness']):>10}{_fmt(s['forbidden_violation_rate']):>9}"
            f"{_fmt(s['refusal_correct_rate']):>9}"
        )
    print("-" * len(header))
    ov = agg["overall"]
    print(
        f"{'OVERALL':<24}{ov['n_cases']:>4}{_fmt(ov['pass_rate']):>8}"
        f"{_fmt(ov['recall_at_k']):>9}{_fmt(ov['precision_at_k']):>8}"
        f"{_fmt(ov['mrr'], pct=False):>7}{_fmt(ov['faithfulness_rate']):>9}"
        f"{_fmt(ov['completeness']):>10}{_fmt(ov['forbidden_violation_rate']):>9}"
        f"{_fmt(ov['refusal_correct_rate']):>9}"
    )
 
    failures = [r for r in results if not r.passed]
    if failures:
        print(f"\n{len(failures)} FAILING CASE(S):")
        print("-" * 100)
        for r in failures:
            print(f"  [{r.test_id}] ({r.category_type}/{r.difficulty}) {r.query}")
            for reason in r.fail_reasons:
                print(f"      - {reason}")
    print()
 
 
def write_json_report(results: list[CaseResult], agg: dict[str, Any], path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aggregate": agg,
        "cases": [
            {
                **{k: v for k, v in asdict(r).items() if k not in ("retrieval", "generation")},
                "retrieval": asdict(r.retrieval),
                "generation": asdict(r.generation),
            }
            for r in results
        ],
    }
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote JSON report: %s", path)

 
## We can also add a function to write CSV report if needed
 
# =============================================================================
# CI gate
# =============================================================================
def check_thresholds(agg: dict[str, Any], args: argparse.Namespace) -> list[str]:
    ov = agg["overall"]
    violations = []
 
    def check(name: str, value: Optional[float], min_ok: Optional[float] = None,
              max_ok: Optional[float] = None):
        if value is None:
            return
        if min_ok is not None and value < min_ok:
            violations.append(f"{name}={value:.3f} is below minimum {min_ok}")
        if max_ok is not None and value > max_ok:
            violations.append(f"{name}={value:.3f} is above maximum {max_ok}")
 
    check("recall_at_k", ov["recall_at_k"], min_ok=args.min_recall)
    check("precision_at_k", ov["precision_at_k"], min_ok=args.min_precision)
    check("completeness", ov["completeness"], min_ok=args.min_completeness)
    check("pass_rate", ov["pass_rate"], min_ok=args.min_pass_rate)
    check("forbidden_violation_rate", ov["forbidden_violation_rate"],
          max_ok=args.max_forbidden_rate)
 
    return violations
 
 
# =============================================================================
# CLI
# =============================================================================
def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Production-grade evaluation harness for the HR-Policy RAG pipeline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dataset", required=True, help="Path to the golden evaluation dataset JSON.")
    p.add_argument("--ingest", action="store_true",
                    help="(Re)ingest the knowledge base into Qdrant before evaluating.")
    p.add_argument("--top-k", type=int, default=getattr(rag, "DEFAULT_TOP_K", 5),
                    help="top_k passed to search_db() for every case.")
    p.add_argument("--category", default=None,
                    help="Only run cases with this category_type (e.g. negative_out_of_scope).")
    p.add_argument("--difficulty", default=None,
                    help="Only run cases with this difficulty (easy|medium|hard).")
    p.add_argument("--test-id", default=None, help="Only run a single case by test_id.")
    p.add_argument("--limit", type=int, default=None, help="Only run the first N matching cases.")
    p.add_argument("--workers", type=int, default=4,
                    help="Concurrent worker threads for running cases (I/O-bound: retrieval + LLM calls).")
    p.add_argument("--judge-model", default=getattr(rag, "LLM_MODEL", None),
                    help="Model used for the LLM-as-judge calls. Defaults to the RAG module's own LLM_MODEL.")
    p.add_argument("--output-dir", default="eval_results",
                    help="Directory to write JSON/CSV reports into.")
    p.add_argument("--min-recall", type=float, default=DEFAULT_MIN_RECALL)
    p.add_argument("--min-precision", type=float, default=DEFAULT_MIN_PRECISION)
    p.add_argument("--min-completeness", type=float, default=DEFAULT_MIN_COMPLETENESS)
    p.add_argument("--min-pass-rate", type=float, default=DEFAULT_MIN_PASS_RATE)
    p.add_argument("--max-forbidden-rate", type=float, default=DEFAULT_MAX_FORBIDDEN_VIOLATION_RATE)
    p.add_argument("-v", "--verbose", action="store_true")
    return p
 
 
def filter_cases(cases: list[dict], args: argparse.Namespace) -> list[dict]:
    filtered = cases
    if args.category:
        filtered = [c for c in filtered if c["category_type"] == args.category]
    if args.difficulty:
        filtered = [c for c in filtered if c.get("difficulty") == args.difficulty]
    if args.test_id:
        filtered = [c for c in filtered if c["test_id"] == args.test_id]
    if args.limit:
        filtered = filtered[: args.limit]
    return filtered
 
 
def main() -> int:
    args = build_arg_parser().parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
 
    if not args.judge_model:
        logger.error("No judge model available (RAG module has no LLM_MODEL and --judge-model "
                      "was not passed).")
        return 2
 
    if args.ingest:
        run_ingest()
 
    verify_collection_ready()
 
    cases = load_golden_dataset(args.dataset)
    cases = filter_cases(cases, args)
    if not cases:
        logger.error("No cases matched the given filters.")
        return 2
 
    logger.info(
        "Running %d case(s) | top_k=%d | judge_model=%s | workers=%d",
        len(cases), args.top_k, args.judge_model, args.workers,
    )
 
    results: list[CaseResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_case, case, args.top_k, args.judge_model): case["test_id"]
            for case in cases
        }
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            test_id = futures[future]
            result = future.result()
            results.append(result)
            completed += 1
            status = "PASS" if result.passed else "FAIL"
            logger.info(
                "[%3d/%3d] %-8s %-8s %.2fs",
                completed, len(cases), status, test_id, result.latency_s,
            )
 
    # Keep report ordering stable / matching input order.
    order = {c["test_id"]: i for i, c in enumerate(cases)}
    results.sort(key=lambda r: order.get(r.test_id, 0))
 
    agg = aggregate(results)
    print_report(results, agg, args.top_k)
 
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    write_json_report(results, agg, str(out_dir / f"rag_eval_{timestamp}.json"))
    violations = check_thresholds(agg, args)
    if violations:
        print("THRESHOLD VIOLATIONS (CI gate failed):")
        for v in violations:
            print(f"  - {v}")
        return 1
 
    print("All configured thresholds met.")
    return 0
 
 
if __name__ == "__main__":
    sys.exit(main())
 

