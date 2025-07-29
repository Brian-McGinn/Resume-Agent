from docling.document_converter import DocumentConverter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from sqlalchemy import create_engine, text
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import json
import os

from sqlalchemy import create_engine, text

def delete_all_documents(connection_string: str):
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM langchain_pg_embedding;")
        )
        conn.commit()

def llmDocSplit(documents):
    # Prepare the prompt for the LLM to split and index the document
    llm_prompt = f"""
    You are an expert at text chunking and indexing. Given the following document, 
    Start chunking the document into sections based on headers.
    Use the headers as the index categories.
    Break the chunk sections into a list by using new lines, periods, and other delimiters.
    Return ONLY a JSON array of objects, each with "index" and "chunk" fields, like:
    [
    {{"index": "Summary", "chunk": ["..."] }},
    {{"index": "Core Skills", "chunk": ["..."] }},
    {{"index": "Professional Experience", "chunk": ["..."] }}
    ]
    Document:
    \"\"\"
    {documents}
    \"\"\"
    """

    llm = Ollama(model="llama3.1")  # or your preferred model

    response = llm.invoke(llm_prompt)
    # Try to extract the JSON from the response
    try:
        # Find the first and last brackets to extract the JSON array
        start = response.find('[')
        end = response.rfind(']')
        if start != -1 and end != -1:
            json_str = response[start:end+1]
            indexed_chunks = json.loads(json_str)
        else:
            indexed_chunks = []
            print("Could not find JSON array in LLM response.")
    except Exception as e:
        indexed_chunks = []
        print(f"Error parsing LLM response as JSON: {e}")

    return indexed_chunks

source = "Brian_McGinn_Resume.pdf"  # document per local path or URL
converter = DocumentConverter()
result = converter.convert(source)
documents = result.document.export_to_markdown()
# loader = PyPDFLoader(source)
# documents = loader.load()

# llm chunking
from langchain_community.llms import Ollama

if documents:
    document_embedder = OllamaEmbeddings(model="nomic-embed-text")
#     documents_json = llmDocSplit(documents)
    
#     # Convert the JSON output into LangChain Document objects
#     docs = []
#     for chunk in documents_json:
#         # Each chunk["chunk"] is a list of strings, join them for the content
#         content = "\n".join(chunk.get("chunk", []))
#         metadata = {"index": chunk.get("index", "")}
#         docs.append(Document(page_content=content, metadata=metadata))

#     # Try to use PGVector with proper database setup
    CONNECTION_STRING = "postgresql://vector_admin:Resume_Pass@localhost:5432/resume_agent"
#     # Use JSONB for metadata to avoid deprecation warning and enable efficient querying.
#     delete_all_documents(CONNECTION_STRING)

#     vectorstore = PGVector.from_documents(
#         documents=docs,
#         embedding=document_embedder,
#         collection_name="resume_embeddings",
#         connection_string=CONNECTION_STRING,
#         use_jsonb=True,  # Explicitly use JSONB for metadata
#     )

    vectorstoreget = PGVector.from_existing_index(
        collection_name="resume_embeddings",
        connection_string=CONNECTION_STRING,
        embedding=document_embedder
    )

    all_docs = vectorstoreget.similarity_search(query="", k=100)

    # Print results
    context = "\n".join([doc.page_content for doc in all_docs])
    clean_context = context.strip()

    del vectorstore
    del vectorstoreget