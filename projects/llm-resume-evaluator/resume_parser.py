from llm_utils import parse_query
from pydantic import BaseModel

class experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None 
    description: str | None = None
    skills_used: list[str] = []

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years: float | None = None
    skills: list[str] = []
    experiences: list[experience] = []
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []


resume_schema = Resume.model_json_schema()

system_prompt = f"""
ROLE: You are an expert RESUME PARSER.

TASK: You will be provided with a resume, and your task is to analyze & extract the structured information from it, based on its meaning not only on exact section headers.  Different resumes may use different headings.
 For example:
    - Experience
    - Professional Experience
    - Work History
    - Employment
    - Internships
 These may all contain relevant experience. Skills may also appear in the skills section, work experience, internships or projects.

OUTPUT FORMAT: Return ONLY the structured information in JSON format, adhering to the following schema: {resume_schema}

CONSTRAINTS:
- The output must be valid JSON and conform to the provided schema. (Do not return the schema itself in the output)
- Do not include any additional text, explanations, or commentary in the output. (Do not invent information)
- If a value field is not present in the resume, return null. 
- If information for a list is missing, return an empty list as appropriate.
- Include Internships in the experiences list, and include the skills used in each experience if mentioned. Extract skills mentioned across the entire resume, including in the skills section, work experience, internships or projects. If a skill is mentioned in multiple places, include it only once in the skills list.
"""


def parse_resume(resume_text: str):

    user_prompt = f"""
    Analyze the following Resume.

    RESUME:
    {resume_text}   
    """

    parsed_resume = parse_query(system_prompt, user_prompt)
    return parsed_resume