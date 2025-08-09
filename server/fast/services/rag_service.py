from langchain_nvidia_ai_endpoints.embeddings import NVIDIAEmbeddings
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.documents import Document
from langchain_community.vectorstores.pgvector import PGVector
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
from sqlalchemy import create_engine, text
import os
import json

EMBEDDING_MODEL = "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1"
CONNECTION_STRING = "postgresql://vector_admin:Resume_Pass@pgvector-db:5432/resume_agent"
COLLECTION_NAME = "resume_embeddings"
document_embedder = NVIDIAEmbeddings(model=EMBEDDING_MODEL, truncate="NONE") # Can use other supported models

def delete_all_documents():
    engine = create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        # Check if the table exists before attempting to delete
        result = conn.execute(
            text("SELECT to_regclass('public.langchain_pg_embedding');")
        )
        table_exists = result.scalar()
        if table_exists:
            conn.execute(
                text("DELETE FROM langchain_pg_embedding;")
            )
            conn.commit()

def setEmbeddings(file):
    """Handle message sending request."""
    try:
        # Configure pipeline to disable OCR
        pipeline_options = PdfPipelineOptions(
            do_ocr=False  # Disable OCR entirely
        )
        # Create converter without OCR
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )
        result = converter.convert(os.path.join("uploads", file.filename))
        documents = result.document.export_to_markdown()

        print(f"Setting embeddings for resume.")
        # Split the resume into chunks and save the embeddings to the local vectorstore
        if documents:
            documents_json = llmDocSplit(documents)
            # Convert the JSON output into LangChain Document objects
            docs = []
            for chunk in documents_json:
                # Each chunk["chunk"] is a list of strings, join them for the content
                content = "\n".join(chunk.get("chunk", []))
                metadata = {"index": chunk.get("index", "")}
                docs.append(Document(page_content=content, metadata=metadata))

            # TODO: enhance indexing to handle multple resumes. Currently hold only one
            delete_all_documents()

            vectorstore = PGVector.from_documents(
                documents=docs,
                embedding=document_embedder,
                collection_name=COLLECTION_NAME,
                connection_string=CONNECTION_STRING,
                use_jsonb=True,  # Explicitly use JSONB for metadata
            )

            del vectorstore

        print(f"Embeddings set for resume.")
    except Exception as e:
        print(f"Failed to llm {str(e)}")
        print(f"Failed to set embeddings for resume.")
        raise RuntimeError(f"Error getting AI response: {str(e)}")

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

    llm = ChatNVIDIA(model="nvidia/llama-3.3-nemotron-super-49b-v1", streaming=False, max_tokens=4096)
    response = llm.invoke(llm_prompt).content
    # Try to extract the JSON from the response
    try:
        # Find the first and last brackets to extract the JSON array
        print(response)
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

def get_context():
    vectorstore = PGVector.from_existing_index(
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        embedding=document_embedder
    )

    # Get all documents in the vectorstore (no filtering)
    all_docs = vectorstore.similarity_search(query="Get all vectors", k=1000)  # Large k to get all, or use a method to fetch all if available

    del vectorstore

    # For each doc, try to get its index value from metadata, and append both index and content in order
    context_parts = []
    for doc in all_docs:
        index_value = ""
        if hasattr(doc, "metadata") and doc.metadata and "index" in doc.metadata:
            index_value = str(doc.metadata["index"])
        # Append index and content, separated by a newline for clarity
        if index_value:
            context_parts.append(f"{index_value}:\n{doc.page_content}")
        else:
            context_parts.append(doc.page_content)

    context = "\n\n".join(context_parts)
    clean_context = context.strip()
    print(f"Context with all vectorstore rows and index values retrieved for resume from postgres vectorstore.")

    return clean_context