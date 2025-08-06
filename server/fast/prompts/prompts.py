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

automate_prompt = HumanMessagePromptTemplate.from_template(
    """
    Use the job_scraper_get_jobs MCP tool to get jobs by filling the job_scraper_request with the following parameters:
    - search_term: {search_term}
    - location: {location}
    - results_wanted: {results_wanted}
    - hours_old: {hours_old}
    - country_indeed: {country_indeed}
    Return ONLY the tool output, exactly as it was returned, in the following JSON format:
    [
        {{
            "title": "string",
            "company": "string",
            "job_url": "string"
        {{
    ]
    If there are multiple jobs, return a list of such objects. Do not add any extra text or explanation.
    """
)

curate_system_prompt = SystemMessagePromptTemplate.from_template(
    """
    You are a career coach AI assistant. Your task is to evaluate how well a candidate's resume aligns with a specific job description. 
    Your task is to help me secure more job interviews by optimizing my resume to highlight relevant skills and experiences.
    Be fair, detailed, and professional.
    """
)

curate_resume_step_1_compare = HumanMessagePromptTemplate.from_template(
    """
    resume:
    {resume}

    Job_description:
    {job_description}

    recommendations:
    {recommendations}

    Compare the resume to the job_description to identify gaps and generate recommendations for improvement.
    Use the recommendations and identified gaps only as a reference to help improve the curated_resume.
    Do NOT include the recommendations and gaps in the return text.

    IMPORTANT: The contact information at the very top of the resume—including the candidate's name, all location information (such as city, state, or zipcode), phone number, and any links (such as LinkedIn or personal website)—must remain completely unchanged in the curated_resume. Do not alter, remove, or add to this contact information in any way. The candidate's name must always be present at the very top of the curated_resume, exactly as it appears in the original resume.

    Do NOT modify any content from the resume except for rearranging and highlighting relevant information as described below.

    Create a new resume by keeping all of the resume content, rearranging the bullet points related to the job_description so they are at the top of the experience section.
    Move the skills in the skill section so skills related to the job_description are highlighted at the top.
    ONLY return the {{curated_resume}}.

    The final resume should fill in a template similar to the following, making sure the candidate's name is at the very top and unchanged:
    Jon Smith | zipcode | phone | linkedin (link)

    Summary:
    Software developer with 10 years of experience at my company. Developed GenAI applications for the past year. Excited to fill the needs for the job_description and contribute to the new team.

    Skills:
    GenAI: Langchain | LangGraph | LLM
    Code: Python | React | Javascript

    Experience:
    job 2024 - present
    - Created a resume agent to assist with job searching and curation

    Education
    - University: Masters in Computer Science 2020
    """
)

curate_resume_step_2_proofread = HumanMessagePromptTemplate.from_template(
    """
    curated_resume:
    {curated_resume}

    Proofread all sections of the curated_resume except for the contact information and education sections. 
    Do not make any changes to the contact information at the top or the education section.
    For all other sections, check for and correct any errors in spelling, grammar, or formatting.
    Pay special attention to consistency in style and detail.
    ONLY return the curated_resume.
    DO NOT include additional notes or proofreading suggestions.
    """
)

curate_resume_step_3_cross_check_original = HumanMessagePromptTemplate.from_template(
    """
    resume:
    {resume}

    curated_resume:
    {curated_resume}

    Do not make any changes to the contact information at the top or the education section.
    Compare bullet points from the original resume and curated_resume
    Only modify mismatch bullet points.
    DO NOT include missing bullet points.
    Make sure curated_resume bullet points align with resume bullet points.
    If bullet points do not match resume rewrite the bullet point to match resume bullet point.
    ONLY return the curated_resume after comparing the bullet points.
    """
)

curate_resume_step_4_format = HumanMessagePromptTemplate.from_template(
    """
    curated_resume:
    {curated_resume}

    Do not make any changes to the contact information at the top or the education section.
    Optimize the curated_resume for Applicant Tracking Systems (ATS).
    Format the curated_resume as a Markdown file:
    - Each section (such as Summary, Skills, Experience, Education) should be a Markdown header using #.
    # In the Skills section, format each skill category as a single line starting with a dash (-), followed by the category name, a colon, and the list of skills separated by |. For example: '- GenAI: Langchain | LangGraph | LLM'
    - Use - for bullet points within each section.
    ONLY return the curated_resume in the specified Markdown format.
    DO NOT include any additional notes or explanations.
    """
)