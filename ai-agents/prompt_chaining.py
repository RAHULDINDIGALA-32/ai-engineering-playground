import os
from dotenv import load_dotenv
from groq import Groq
from time import sleep
import logging


load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set. Please set it in your .env file.")

client = Groq(api_key=my_api_key)

BEST_MODEL = "openai/gpt-oss-120b"
STANDARD_MODEL = "llama-3.3-70b-versatile"

JOB_DESCRIPTION="""
We are hiring a Backend Python Developer.

Requirements:
- Strong Python
- FastAPI or Django
- PostgreSQL
- Docker
- AWS
- REST APIs
- 2+ years of experience
"""

CANDIDATE_RESUME1="""
Name: Rahul Dindigala

Experience:
3 years as a Software Developer.

Skills:
Python, FastAPI, MySQL, Docker,
REST APIs, Git

Projects:
Built a food delivery backend using FastAPI and MySQL.

Deployed applications using Docker.
"""

def call_llm(system_prompt, user_prompt, model=STANDARD_MODEL):
    system_message = {
        "role": "system",
        "content": system_prompt
    }
    user_message = {
        "role": "user",
        "content": user_prompt
    }
    messages = [system_message, user_message]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        llm_answer = response.choices[0].message.content
        return llm_answer
    except Exception as e:
        logging.exception("Failed to call LLM. Error: ", e)
        return None



def step1_resume_extract(resume):
    print("\nSTEP-1: Resume Extraction")
    system_prompt="""
    ROLE:  You are an expert RESUME PARSER. 

    TASK: You will be provided with a Candidates RESUME, and your task is to analyze & extract the Skills from it.

    OUTPUT FORMAT:  Skills should be separated by commas. Just return comma separated skills do not return any other filler information.

    CONSTRAINTS:
- Do not include any additional text, explanations, or commentary in the output.
- Do not invent information. Only extract what is stated in the RESUME.

    FALLBACK: If NO skill is found in Resume, return empty string. No other extra fillers.
"""
    user_prompt = f"""
    Extract the skills from the resume: 
    {resume}
    """

    return call_llm(system_prompt, user_prompt, model=STANDARD_MODEL)


def step2_JD_extract(jd):
    print("\nSTEP-2: Job Description Extraction")
    system_prompt="""
    ROLE: You are an professional HR assistant. 
    
    TASK: You will be provided with a Job Description, and your task is to analyze & extract the Skills from it.
    
    OUTPUT FORMAT:  Skills should be separated by commas. Just return comma separated skills do not return any other filler information.
    
    CONSTRAINTS:
    -Do not invent any skills by yourself
    - Do not include any additional text, explanations, or commentary in the output.
    - Do not invent information. Only extract what is stated in the RESUME.
    
    FALLBACK: If NO skill is found in Job Dscription, return empty string. No other extra fillers.
    """
    user_prompt=f"""
    Extract the skills from Job Dscription:
    {jd}
    """

    return call_llm(system_prompt, user_prompt, model=STANDARD_MODEL)


def step3_match(candidate, jd):
    print("\nSTEP-3: Match & Scoring")
    system_prompt="""
    ROLE: You are a senior HR recruiter with extensive experience in evaluating candidates skills and matching candidates to job descriptions. 

    TASK: Your task is to assess the alignment between a candidate's skills and skills mentioned in job description , providing a final score between 1 and 100. also produce a short verdict whether the candidate is a good fit for the role.

    Return ONLY the final_score & final_verdict.

    CONSTRAINTS:
    - Keep the response concise and easy to read.
    - Strictly use only the information provided in the resume skills and job description skills for evaluation.
    - DO not assume or invent any information
    """
    user_prompt=f"""
    Match and score the Candidate: {candidate} against the Job Description: {jd}.
    """

    return call_llm(system_prompt, user_prompt, model=BEST_MODEL)



candidate1_skills = step1_resume_extract(CANDIDATE_RESUME1)
print("Candidate 1 Skills: ",candidate1_skills)
sleep(2)

jd_skills = step2_JD_extract(JOB_DESCRIPTION)
print("Required Skills (JD): ", jd_skills) 
sleep(2)

match_details = step3_match(candidate1_skills, jd_skills)
print(match_details)






