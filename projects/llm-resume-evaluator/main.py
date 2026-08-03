import time
from pathlib import Path
import json

from resume_reader import read_resume
from resume_parser import parse_resume
from jd_parser import parse_job_description
from evaluator import evaluate_resume


job_description_text = """
Description
Do you want to solve real customer problems through innovative technology? Do you enjoy working on scalable services in a collaborative team environment? Do you want to see your code directly impact millions of customers worldwide?

At Amazon, we hire the best minds in technology to innovate and build on behalf of our customers. Customer obsession is part of our company DNA, which has made us one of the world's most beloved brands.

Our Software Development Engineers (SDEs) use modern technology to solve complex problems while seeing their work's impact first-hand. The challenges SDEs solve at Amazon are meaningful and influence millions of customers, sellers, and products globally. We seek individuals passionate about creating new products, features, and services while managing ambiguity in an environment where development cycles are measured in weeks, not years.

At Amazon, we believe in ownership at every level. As an SDE-I, you'll own the entire lifecycle of your code - from design through deployment and ongoing operations. This ownership mindset, combined with our commitment to operational excellence, ensures we deliver the highest quality solutions for our customers.

We're looking for curious minds who think big and want to define tomorrow's technology. At Amazon, you'll grow into the high-impact engineer you know you can be, supported by a culture of learning and mentorship. Every day brings exciting new challenges and opportunities for personal growth.
Key job responsibilities
• Collaborate and communicate effectively with experienced cross-disciplinary Amazonians to design, build, and operate innovative products and services that delight our customers, while participating in technical discussions to drive solutions forward.
• Design and develop scalable solutions using cloud-native architectures and microservices in a large distributed computing environment.
• Participate in code reviews and contribute to technical documentation.
• Build and maintain resilient distributed systems that are scalable, fault-tolerant, and cost-effective.
• Leverage and contribute to the development of GenAI and AI-powered tools to enhance development productivity while staying current with emerging technologies.
• Write clean, maintainable code following best practices and design patterns.
• Work in an agile environment practicing CI/CD principles while participating in operational responsibilities including on-call duties.
• Demonstrate operational excellence through monitoring, troubleshooting, and resolving production issues.
Basic Qualifications
- Experience with at least one general-purpose programming language such as Java, Python, C++, C#, Go, Rust, or TypeScript
- Experience with data structure implementation, basic algorithm development, and/or object-oriented design principles
- Currently has, or is in the process of obtaining a bachelor’s degree in Computer Science, Computer Engineering, Data Science, Information Systems, or related STEM fields
- Must be 18 years of age of older
Preferred Qualifications
- Experience from previous technical internship(s) or demonstrated project experience
- Experience with one or more of the following: AI tools for development productivity, Cloud platforms (preferably AWS), Database systems (SQL and NoSQL), Contributing to open-source projects, Version control systems, Debugging and troubleshooting complex systems
- Demonstrated ability to learn and adapt to new technologies quickly
- Basic understanding of software development lifecycle (SDLC)
- Strong problem-solving and analytical skills
- Excellent written and verbal communication skills
"""

job_description = parse_job_description(job_description_text)

def main():
    print("###################################################################")
    print("Welcome to LLM Resume Evaluator!")

    resume_dir  = Path("resumes")
    results = []
    for resume_path in resume_dir.iterdir():
        if resume_path.suffix.lower() not in [".pdf", ".docx"]:
            continue
        print(f"\nProcessing resume: {resume_path.name}")
        resume_text = read_resume(resume_path)
        parsed_resume = parse_resume(resume_text)
        time.sleep(5)  # Adding a delay to avoid overwhelming the API
        evaluation_result = evaluate_resume(parsed_resume, job_description)
        time.sleep(5) # Adding a delay to avoid overwhelming the API
        results.append({
            "name": json.loads(parsed_resume).get("name"),
            "email": json.loads(parsed_resume).get("email"),
            "score": json.loads(evaluation_result).get("score"),
            "details": json.loads(evaluation_result).get("details"),
        })

    results.sort(
        key = lambda candidate: candidate["score"],
        reverse = True
    )

    top_2_candidates = results[:2]
    bottom_2_candidates = results[-2:]

    print("\nTop 2 Candidates:")
    for candidate in top_2_candidates:
        print(f"Name: {candidate['name']}, Email: {candidate['email']}, Score: {candidate['score']}")
        print(f"Details: {candidate['details']}\n")
    
    print("\nBottom 2 Candidates:")
    for candidate in bottom_2_candidates:
        print(f"Name: {candidate['name']}, Email: {candidate['email']}, Score: {candidate['score']}")
        print(f"Details: {candidate['details']}\n")


if __name__ == "__main__":
    main()
