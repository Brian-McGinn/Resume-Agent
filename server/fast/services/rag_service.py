from langchain_nvidia_ai_endpoints.embeddings import NVIDIAEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
import pickle
import os
import os
from langsmith import Client

EMBEDDING_MODEL = "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1"

# Set up LangSmith client if LANGCHAIN_API_KEY is present in environment
langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
if LANGCHAIN_API_KEY:
    langsmith_client = Client(
            api_key=LANGCHAIN_API_KEY,
            api_url=langsmith_endpoint
        )
else: 
    langsmith_client = None

def log_to_langsmith(message):
    if langsmith_client:
        client.log_message(message)

def setEmbeddings(file):
    """Handle message sending request."""
    try:
        document_embedder = NVIDIAEmbeddings(model=EMBEDDING_MODEL, truncate="NONE") # Can use other supported models
        vector_store_path = "vectorstore.pkl"
        # Load the resume file
        loader = PyPDFLoader(os.path.join("uploads", file.filename))
        documents = loader.load()
        vector_store_exists = os.path.exists(vector_store_path)
        vectorstore = None
        if vector_store_exists:
            os.remove(vector_store_path)
        log_to_langsmith(f"Setting embeddings for resume.")
        # Split the resume into chunks and save the embeddings to the local vectorstore
        if documents:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=0)
            docs = text_splitter.split_documents(documents)
            vectorstore = FAISS.from_documents(docs, document_embedder)
            with open(vector_store_path, "wb") as f:
                pickle.dump(vectorstore, f)
        log_to_langsmith(f"Embeddings set for resume.")
    except Exception as e:
        print(f"Failed to llm {str(e)}")
        log_to_langsmith(f"Failed to set embeddings for resume.")
        raise RuntimeError(f"Error getting AI response: {str(e)}")

def get_context():
    vector_store_path = "vectorstore.pkl"
    vector_store_exists = os.path.exists(vector_store_path)
    vectorstore = None
    if vector_store_exists:
        with open(vector_store_path, "rb") as f:
            log_to_langsmith(f"Getting embeddings for resume.")
            vectorstore = pickle.load(f)
        # Create a retriever
        retriever = vectorstore.as_retriever()
    # Return the entire document embedding (all documents in the vectorstore)
    # TODO: Add additional resumes to the vectorstore based on role (ex. Staff engineer, Architect, Product Manager, etc.).
    # TODO: You will update this retriever to only get resumes relevant to the job description.
    search_results = retriever.vectorstore.docstore._dict.values()
    # Format the context as a string
    context = "\n".join([doc.page_content for doc in search_results])
    clean_context = context.strip()
    log_to_langsmith(f"Context retrieved for resume.")
    return clean_context