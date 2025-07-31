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
    Modify my resume for the job description. Examine the job description carefully and identify keywords and skills that the employer emphasizes. Adjust my resume to highlight my qualifications that match these requirements. This customization shows employers my candidacy aligns well with the job expectations.
    Proofread my tailored resume for any errors in spelling, grammar, or formatting. Pay special attention to consistency in style and detail. Consider asking a friend or using professional services to review my resume. This ensures it is polished and professional.
    Format the new resume to be automated tracking system friendly.

    Here is the candidate's resume:
    {resume}

    Here is the chat history that contains improvements to the resume and previous revisions:
    {improvements}
    
    Here is the job description:
    {job_description}

    Use the assistant's feedback to improve the resume.
    You can add more information to the resume if needed.
    You can also remove information if it is not relevant to the job description.
    Try to improve the resume to make it more relevant to the job description.
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

    IMPORTANT: ONLY return the match score as a single integer value between 0 and 100. Do not include any explanation or additional text.
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