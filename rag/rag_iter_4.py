# RAG with vector embeddings + Vector DB (Qdrant)

# Imports & Environment setup
import os
import logging
import json
from typing import Optional, List

from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, PayloadSchemaType


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRAT_URL = os.getenv("QDRANT_URL")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")
elif not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY environment variable is not set. Please set it in your .env file.")
elif not QDRAT_URL:
    raise ValueError("QDRANT_URL environment variable is not set. Please set it in your .env file.")


# Configuration
COLLECTION_NAME = "Knowledge_base"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_SIZE = 384

LLM_MODEL = "openai/gpt-oss-120b"

DEFAULT_TOP_K = 5
DEFAULT_SCORE_THRESHOLD = None

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# Connect to Qdrant (Vector DB)
qdrant_client = QdrantClient(
    url=QDRAT_URL,
    api_key=QDRANT_API_KEY
)

logging.info("Connected to Qdrant Cloud!!")

# Load Embedding Model
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME) # 384 dims (features)

logging.info(
    "Embedding model loaded: %s!",
    EMBEDDING_MODEL_NAME
)

# Connect to Groq
llm_client = Groq(api_key=GROQ_API_KEY)

logging.info("Groq client initialized")


# Create Qdrant Collection
def create_collection(recreate: bool = True):

    exists = qdrant_client.collection_exists(
        COLLECTION_NAME
    )

    if exists and recreate:

        logging.info(
            "Deleting existing collection: %s",
            COLLECTION_NAME
        )

        qdrant_client.delete_collection(
            COLLECTION_NAME
        )

        exists = False

    if not exists:

        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_SIZE,
                distance=Distance.COSINE
            )
        )

        logging.info(
            "Created collection: %s",
            COLLECTION_NAME
        )

    else:

        logging.info(
            "Using existing collection: %s",
            COLLECTION_NAME
        )

    logging.info(
        "Embedding Vector Size: %s",
        EMBEDDING_SIZE
    )

    logging.info("Distance: COSINE")


# Create Payload Indexes (used by filters wjile searching)
def create_payload_indexes():

    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="category",
        field_schema=PayloadSchemaType.KEYWORD
    )

    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="subcategory",
        field_schema=PayloadSchemaType.KEYWORD
    )

    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="is_active",
        field_schema=PayloadSchemaType.BOOL
    )

    logging.info(
        "Payload indexes created."
    )


# Load knowledge Base
def load_knowledge_base(file_path: str = "knowledge_base.json"):
 
    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    documents = data.get("policies", [])

    if not documents:
        raise ValueError(
            "No policies found in knowledge base."
        )

    logging.info(
        "Loaded %d policies",
        len(documents)
    )

    return documents


# Build Searchable Text
def build_embedding_text(document: dict) -> str:
    """
    Build a rich textual representation of a policy.

    This is what gets embedded into the vector space.

    We include:
    - title
    - category
    - subcategory
    - description
    - keywords
    - structured policy details
    """

    parts = []

    # Basic metadata
    parts.append(
        f"Policy ID: {document.get('id', '')}"
    )

    parts.append(
        f"Title: {document.get('title', '')}"
    )

    parts.append(
        f"Category: {document.get('category', '')}"
    )

    parts.append(
        f"Subcategory: {document.get('subcategory', '')}"
    )

    # Main description
    parts.append(
        f"Description: {document.get('description', '')}"
    )

    # Keywords
    filters = document.get("filters", {})

    keywords = filters.get("keywords", [])

    if keywords:
        parts.append(
            f"Keywords: {', '.join(keywords)}"
        )

    # Structured fields
    structured_fields = [
        "benefit",
        "eligibility",
        "requirements",
        "carry_forward",
        "notice_period",
        "coverage",
        "working_hours",
        "working_days",
        "probation",
        "evaluation_criteria",
        "notification",
        "confidential_information",
        "requirements",
        "compensation",
        "payment_schedule",
        "eligible_expenses",
        "calculation_factors",
        "work_from_office_days",
        "work_from_home_days",
        "remote_work",
        "medical_certificate"
    ]

    for field in structured_fields:

        value = document.get(field)

        if value is not None:

            parts.append(
                f"{field}: "
                f"{json.dumps(value, ensure_ascii=False)}"
            )

    return "\n".join(parts)


# Ingest Knowledge Base (Create embeddings and upload to Qdrant.)
def ingest_knowledge_base(documents: List[dict]):
    
    # Build searchable text
    document_texts = [
        build_embedding_text(document)
        for document in documents
    ]

    logging.info(
        "Building embeddings for %d documents",
        len(document_texts)
    )

    # Generate embeddings
    embeddings = embedding_model.encode(
        document_texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    logging.info(
        "Generated embeddings: count=%d, dimensions=%d",
        len(embeddings),
        len(embeddings[0])
    )

   
    # Create Qdrant points
    points = []

    for i, document in enumerate(documents):

        payload = {
            # Fields used for retrieval/debugging
            "id": document.get("id"),
            "title": document.get("title"),
            "category": document.get("category"),
            "subcategory": document.get("subcategory"),
            "description": document.get("description"),

            # Used to exclude deprecated policies
            "is_active": document.get(
                "is_active",
                True
            ),

            # Search representation
            "search_text": document_texts[i],

            # Keep the complete original policy
            "document": document
        }

        point = PointStruct(
            id=i + 1,
            vector=embeddings[i].tolist(),
            payload=payload
        )

        points.append(point)

    # Upload
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True
    )

    logging.info(
        "Uploaded %d policies to Qdrant",
        len(points)
    )


# Build Qdrant Search Filter
def build_filter(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    is_active: Optional[bool] = True
):
    """
    Build a Qdrant filter dynamically.

    Default behavior:
        is_active=True

    Optional:
        category
        subcategory
    """

    conditions = []

    # Active policy filter
    if is_active is not None:

        conditions.append(
            FieldCondition(
                key="is_active",
                match=MatchValue(
                    value=is_active
                )
            )
        )

    # Category filter
    if category is not None:

        conditions.append(
            FieldCondition(
                key="category",
                match=MatchValue(
                    value=category
                )
            )
        )

    # Subcategory filter
    if subcategory is not None:

        conditions.append(
            FieldCondition(
                key="subcategory",
                match=MatchValue(
                    value=subcategory
                )
            )
        )

    # No conditions
    if not conditions:
        return None

    return Filter(
        must=conditions
    )


# Vector Search
def search_db(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    is_active: Optional[bool] = True,
    score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD
):
    """
    Semantic search against Qdrant.
    """

    # Embed query
    query_vector = embedding_model.encode(
        query,
        normalize_embeddings=True
    )

    # Build filter
    query_filter = build_filter(
        category=category,
        subcategory=subcategory,
        is_active=is_active
    )

    # Search
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector.tolist(),
        query_filter=query_filter,
        limit=top_k,
        score_threshold=score_threshold,
        with_payload=True
    ).points

    return results

# Debug Retrieval
def print_search_results(
    query: str,
    results
):
    """
    Print retrieval results for debugging.
    """

    print("\n")
    print("=" * 80)
    print("RETRIEVAL DEBUG")
    print("=" * 80)

    print(f"Query: {query}")
    print(f"Results: {len(results)}")

    if not results:

        print("\nNo documents retrieved.")
        return

    for index, result in enumerate(
        results,
        start=1
    ):

        payload = result.payload

        print("\n" + "-" * 80)

        print(f"Rank: {index}")
        print(
            f"Score: {result.score:.4f}"
        )

        print(
            f"Policy ID: "
            f"{payload.get('id')}"
        )

        print(
            f"Title: "
            f"{payload.get('title')}"
        )

        print(
            f"Category: "
            f"{payload.get('category')}"
        )

        print(
            f"Subcategory: "
            f"{payload.get('subcategory')}"
        )

        print(
            f"Active: "
            f"{payload.get('is_active')}"
        )

        print(
            f"Description: "
            f"{payload.get('description')}"
        )


# Extract Context
def extract_context(results) -> str:
    """
    Convert retrieved policies into LLM context.
    """

    if not results:
        return ""

    contexts = []

    for result in results:

        payload = result.payload

        policy_id = payload.get(
            "id",
            "UNKNOWN"
        )

        title = payload.get(
            "title",
            ""
        )

        category = payload.get(
            "category",
            ""
        )

        subcategory = payload.get(
            "subcategory",
            ""
        )

        description = payload.get(
            "description",
            ""
        )

        document = payload.get(
            "document",
            {}
        )

        contexts.append(
            f"""
Policy ID: {policy_id}

Title:
{title}

Category:
{category}

Subcategory:
{subcategory}

Description:
{description}

Policy Details:
{json.dumps(
    document,
    indent=2,
    ensure_ascii=False
)}
""".strip()
        )

    return "\n\n" + "\n\n".join(
        f"--- Policy {i} ---\n{context}"
        for i, context in enumerate(
            contexts,
            start=1
        )
    )



# Make LLM Call

# LLM System Prompt
SYSTEM_PROMPT = """
ROLE: You are an employee-policy question answering assistant.

TASK: Answer the user's question using ONLY the provided context.

Rules:

1. Do not use outside knowledge.

2. Do not hallucinate.

3. Do not infer a policy that is not explicitly supported
   by the provided context.

4. If the answer cannot be found in the provided context,
   respond exactly:
   "I don't know based on the provided context."

5. Prefer active policies.

6. If a policy contains eligibility requirements,
   conditions, limits, amounts, or time periods,
   explicitly mention the relevant condition.

7. For comparison questions, clearly state the differences
   between the relevant policies.

8. For questions involving multiple benefits or policies,
   include all relevant policies supported by the context.

9. Keep the answer concise and direct.

10. Never mention the retrieval process, vector database,
    embeddings, or context to the user.
"""


def call_llm(
    query: str,
    context: str
) -> str:

    if not context.strip():

        return (
            "I don't know based on the provided context."
        )

    user_prompt = f"""
Context:
{context}

Question:
{query}
"""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    try:

        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0
        )

        answer = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        return answer

    except Exception:

        logging.exception(
            "Failed to call Groq LLM"
        )

        return (
            "I don't know based on the provided context."
        )


# ============================================================
# COMPLETE RAG PIPELINE
# ============================================================

def rag_pipeline(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    score_threshold: Optional[float] = DEFAULT_SCORE_THRESHOLD,
    debug: bool = True
):
    """
    Complete RAG pipeline:

        Query
          ↓
        Embedding
          ↓
        Qdrant retrieval
          ↓
        Active-policy filter
          ↓
        Context construction
          ↓
        LLM Call
          ↓
        Answer
    """

    # 1. Retrieve
    results = search_db(
        query=query,
        top_k=top_k,
        category=category,
        subcategory=subcategory,
        is_active=True,
        score_threshold=score_threshold
    )

    # 2. Debug retrieval
    if debug:

        print_search_results(
            query=query,
            results=results
        )

    # 3. No retrieval result
    if not results:

        return (
            "I don't know based on the provided context."
        )

    # 4. Build context
    context = extract_context(
        results
    )

    if debug:

        print("\n")
        print("=" * 80)
        print("LLM CONTEXT")
        print("=" * 80)
        print(context)

    # 5. Generate answer
    answer = call_llm(
        query=query,
        context=context
    )

    return answer


## Initialize 
if __name__ == "__main__":

  
    # Load policies
    documents = load_knowledge_base(
        "knowledge_base.json"
    )

    # Recreate collection
    create_collection(
        recreate=True
    )

    # Create payload indexes
    create_payload_indexes()

    # Ingest policies
    ingest_knowledge_base(
        documents
    )

    # TEST QUERIES
    test_queries = [

        # 1. DIRECT / SIMPLE QUERY
        "How many paid leave days do employees get per year?",

        # 2. CONDITIONAL QUERY
        "When can an employee claim home internet reimbursement?",

        # 3. MULTI-DOCUMENT QUERY
        "What benefits are available to employees who work remotely?",

        # 4. COMPARISON QUERY
        "What is the difference between the normal notice period and the probation notice period?",

        # 5. NEGATIVE / HALLUCINATION TEST
        "Does the company provide dental insurance?"
    ]

  
    # RUN TESTS
    for query in test_queries:

        print("\n\n")
        print("#" * 80)
        print("QUERY")
        print("#" * 80)

        print(query)

        answer = rag_pipeline(
            query=query,
            top_k=5,
            debug=True
        )

        print("\n")
        print("#" * 80)
        print("ANSWER")
        print("#" * 80)

        print(answer)

