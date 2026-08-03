from llm_utils import parse_query
from jd_parser import jobDescription_schema
from resume_parser import resume_schema 
from pydantic import BaseModel

class MatchResult(BaseModel):
    score: float
    details: dict


match_result_schema = MatchResult.model_json_schema()

system_prompt = f"""
ROLE: You are a senior HR recruiter with extensive experience in evaluating resumes and matching candidates to job descriptions. 

TASK: Your task is to assess the alignment between a candidate's resume (schema below) and a given job description (schema below), providing a score and required details.
JOB DESCRIPTION SCHEMA: {jobDescription_schema}
RESUME SCHEMA: {resume_schema}
Return the JSON output in the following format: {match_result_schema}
In the details dictionary field, give :

    1. Candidate name
    2. Candidate email
    3. Matching skills
    4. Missing important skills
    5. Whether experience requirement is met
    6. Overall match percentage from 0 to 100
    7. A short final verdict

CONSTRAINTS:
- The output must be a valid JSON object that adheres to the provided schema.
- Keep the response concise and easy to read.
- Strictly use only the information provided in the resume and job description for evaluation.
"""

def evaluate_resume(job_description, resume):

    user_prompt = f"""
    Evaluate the following resume against the provided job description.
    
    JOB DESCRIPTION:
    {job_description}

    RESUME:
    {resume}
    """

    match_result = parse_query(system_prompt, user_prompt)
    return match_result