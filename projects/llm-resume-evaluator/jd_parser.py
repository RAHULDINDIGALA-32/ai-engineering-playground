from llm_utils import parse_query
from pydantic import BaseModel

class JobDescription(BaseModel):
    role:str
    required_skills: list[str]
    preferred_skills: list[str]
    minimum_experience: str
    education_requirements: list[str]
    responsibilities: list[str]

jobDescription_schema = JobDescription.model_json_schema()

system_prompt = f"""
ROLE: You are an expert HR assistant. 

TASK: You will be provided with a job description, and your task is to analyze & extract the structured information from it.

OUTPUT FORMAT: Return ONLY the structured information in JSON format, adhering to the following schema:
{jobDescription_schema}

CONSTRAINTS:
- The output must be valid JSON and conform to the provided schema. (Do not return the schema itself in the output)
- Do not include any additional text, explanations, or commentary in the output.
- Fill the schema with actual information extracted from the job description. If a field is not present in the job description, return null. If information for a list is missing, return an empty list as appropriate.
- Do not invent information. Only extract what is explicitly stated in the job description.

"""

def parse_job_description(job_description_text: str):

    user_prompt = f"""
    Analyze the following Job Description.

    JOB DESCRIPTION:
    {job_description_text}   
    """

    parsed_job_description = parse_query(system_prompt, user_prompt)
    return parsed_job_description
    
