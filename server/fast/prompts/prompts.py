from services.rag_service import get_context
from typing import List, Dict
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate

system_prompt = SystemMessagePromptTemplate.from_template(
    """
    You are a career coach AI assistant. Your task is to evaluate how well a candidate's resume aligns with a specific job description. 
    Your task is to help me secure more job interviews by optimizing my resume to highlight relevant skills and experiences.
    Be fair, detailed, and professional. Always provide a numeric match score from 1 (poor fit) to 100 (excellent fit), followed by a concise rationale
    """
)

resume_review_prompt = HumanMessagePromptTemplate.from_template(
    """
    IMPORTANT: Only use the context provided to compare against the job description.

    Here is the candidate's resume (retrieved context):
    {context}

    And here is the job description:
    {question}

    How well does this candidate match the job? Provide a match score and justification.
    Include any suggestions for improvements to the resume.
    """
)

resume_revise_prompt = HumanMessagePromptTemplate.from_template(
    """
    Modify my resume for the job description. Carefully review the job description and identify the most important keywords and skills. Update my resume to highlight my qualifications that best match these requirements. Make sure the resume is formatted to be friendly for automated tracking systems (ATS).

    Here is the candidate's resume:
    {resume}

    Here is the chat history that contains improvements to the resume and previous revisions:
    {improvements}
    
    Here is the job description:
    {job_description}

    Use the assistant's feedback and your expertise to improve the resume. You may add or remove information as needed to make the resume more relevant to the job description.

    IMPORTANT: Only return the updated resume in markdown format. Do not include any extra explanation, commentary, or formatting outside of the markdown resume itself.
    """
)

generate_job_score_prompt = HumanMessagePromptTemplate.from_template(
    """
    IMPORTANT: Only use the context provided to compare against the job description.

    Here is the candidate's resume (retrieved context):
    {context}

    And here is the job description:
    {question}

    Based on the information above, provide a single integer match score from 0 to 100 indicating how well the candidate matches the job.

    Return your answer as a JSON object in the following format:
    {{
        "score": <integer between 0 and 100>,
        "content": "<A concise explanation of the score, including job comparisons, suggestions, and recommendations.>"
    }}

    Replace <integer between 0 and 100> with the actual score, and <...> with your generated content. Do not include any extra text outside the JSON object.
    """
)

automate_prompt ="""
    Using job_scraper_get_jobs tool get the top 5 software engineer jobs.
    Return ONLY the tool output, exactly as it was returned, in the following JSON format:
    [
        {
            "title": "string",
            "company": "string",
            "job_url": "string"
        }
    ]
    If there are multiple jobs, return a list of such objects. Do not add any extra text or explanation.
    """