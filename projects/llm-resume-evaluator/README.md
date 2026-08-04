# LLM Resume Evaluator

An LLM-powered Python project that parses resumes, extracts structured job-description requirements, and scores candidates against a target role. The project is designed as a practical AI engineering exercise for combining document ingestion, schema-guided LLM extraction, and candidate-job matching.

## Overview

`llm-resume-evaluator` reads resume files from a local `resumes/` directory, converts each resume into structured JSON, parses a job description into structured requirements, and then uses an LLM to evaluate how closely each candidate matches the role.

The current implementation evaluates resumes against a sample job description defined in `main.py` and prints the top and bottom candidates by score.

## Features

- Reads resumes from PDF and DOCX files.
- Extracts resume text using `pypdf` and `python-docx`.
- Uses Pydantic schemas to guide structured LLM outputs.
- Parses job descriptions into role, skills, experience, education, and responsibility fields.
- Evaluates each candidate against the job description using the Groq API.
- Produces a score, matched skills, missing skills, experience assessment, match percentage, and final verdict.
- Sorts candidates by score and prints the top and bottom matches.

## Project Structure

```text
llm-resume-evaluator/
|-- evaluator.py        # Scores parsed resumes against a parsed job description
|-- jd_parser.py        # Extracts structured fields from a job description
|-- llm_utils.py        # Groq client configuration and shared LLM call helper
|-- main.py             # CLI entry point and sample job description
|-- resume_parser.py    # Extracts structured fields from raw resume text
|-- resume_reader.py    # Reads text from PDF and DOCX resumes
|-- resumes/            # Local input folder for candidate resumes
|-- pyproject.toml      # Project metadata and dependencies
`-- uv.lock             # Locked dependency versions
```

## How It Works

1. `main.py` defines the target job description.
2. `jd_parser.py` converts the job description into structured JSON.
3. `resume_reader.py` loads each `.pdf` or `.docx` file from the `resumes/` directory.
4. `resume_parser.py` converts raw resume text into a structured candidate profile.
5. `evaluator.py` compares the parsed resume with the parsed job description.
6. Results are sorted by score and printed in ranked groups.

## Requirements

- Python 3.11 or later
- A Groq API key
- Resume files in PDF or DOCX format

## Setup

From the project directory:

```bash
cd projects/llm-resume-evaluator
```

Install dependencies with `uv`:

```bash
uv sync
```

Alternatively, install with `pip`:

```bash
pip install -e .
```

Create a `.env` file in the project directory or set the environment variable in your shell:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Usage

Place candidate resumes in the `resumes/` directory:

```text
resumes/
|-- candidate_1.pdf
|-- candidate_2.docx
`-- candidate_3.pdf
```

Run the evaluator:

```bash
uv run python main.py
```

Or, if dependencies are already installed in your active environment:

```bash
python main.py
```

The script prints ranked candidate summaries similar to:

```text
Top 2 Candidates:
Name: Candidate Name, Email: candidate@example.com, Score: 87.5
Details: {...}

Bottom 2 Candidates:
Name: Candidate Name, Email: candidate@example.com, Score: 42.0
Details: {...}
```

## Configuration

### LLM Provider

The project uses the Groq Python SDK in `llm_utils.py`.

Default model:

```python
DEFAULT_MODEL = "openai/gpt-oss-120b"
```

To use a different Groq-supported model, update `DEFAULT_MODEL` in `llm_utils.py`.

### Job Description

The job description is currently stored as a multiline string in `main.py`:

```python
job_description_text = """
...
"""
```

Replace this value with another job description to evaluate resumes against a different role.

### Resume Inputs

Supported file extensions:

- `.pdf`
- `.docx`

Unsupported files in the `resumes/` directory are skipped.

## Output Schema

Each evaluation returns a JSON object with:

- `score`: Numeric candidate-role match score.
- `details`: A dictionary containing candidate details, matched skills, missing skills, experience fit, overall match percentage, and a concise verdict.

Resume parsing is guided by a schema that includes:

- Name
- Email
- Phone
- Total experience
- Skills
- Experience history
- Education
- Projects
- Certifications

Job-description parsing is guided by a schema that includes:

- Role
- Required skills
- Preferred skills
- Minimum experience
- Education requirements
- Responsibilities

## Notes and Limitations

- The evaluator depends on LLM output quality, so results should be treated as decision support rather than a final hiring decision.
- The current implementation includes short delays between LLM calls to avoid overwhelming the API.
- The job description is hard-coded in `main.py`; moving it to a file or CLI argument would make the project easier to reuse.
- Resume parsing works best when files contain extractable text. Scanned image-only resumes may require OCR before evaluation.
- Candidate ranking is only as reliable as the extracted resume text, job description quality, and evaluation prompt.

## Future Improvements

- Accept job descriptions from a file or command-line argument.
- Export ranked results to JSON or CSV.
- Add a web or Streamlit interface for uploading resumes.
- Add OCR support for scanned PDFs.
- Add automated tests for parsing and ranking behavior.
- Support configurable top-N candidate reporting.

## Tech Stack

- Python
- Groq API
- Pydantic
- pypdf
- python-docx
- python-dotenv / dotenv
- uv
