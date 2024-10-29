# routers/rag_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pinecone import Pinecone, ServerlessSpec
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from utils.pdf_processor import get_pdf_documents
from utils.helper_functions import set_environment_variables, clear_cache_directory
from llama_index.vector_stores.pinecone import PineconeVectorStore
from io import BytesIO
import os
import requests

# Set up router
router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)

# Initialize environment variables
set_environment_variables()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Specify directory for saving the temporary files
CACHE_DIR = "./.cache"
TMP_DIR = os.path.join(CACHE_DIR, "tmp")

# Create the directories if they don't exist
os.makedirs(TMP_DIR, exist_ok=True)

# Data model to receive PDF link and ID
class PDFLink(BaseModel):
    pdf_link: str
    pdf_id: str

class QueryRequest(BaseModel):
    question: str
    pdf_id: str
    index_type: str 

@router.get("/check-index")
async def check_index(pdf_id: str):
    """Check if an index exists for the given PDF ID in Pinecone."""
    try:
        index_name = f"pdf-index-{pdf_id}"
        if index_name in pc.list_indexes().names():
            return {"index_exists": True}
        else:
            return {"index_exists": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking index: {str(e)}")

def initialize_settings():
    Settings.embed_model = NVIDIAEmbedding(model="nvidia/nv-embedqa-e5-v5", truncate="END")
    Settings.llm = NVIDIA(model="meta/llama3-70b-instruct")
    Settings.text_splitter = SentenceSplitter(chunk_size=650)

def create_index(documents, pdf_id):
    index_name = f"pdf-index-{pdf_id}"

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    
    vector_store = PineconeVectorStore(index_name=index_name)
    
    # Create a storage context without specifying persist_dir if not needed locally
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Create the index directly in Pinecone
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    
    return index

@router.post("/process-pdf")
async def process_pdf_link(data: PDFLink):
    """Process a given PDF link, create an index, and return success message."""
    try:
        pdf_id = str(data.pdf_id)

        # Clear the temporary cache directory before processing
        clear_cache_directory(TMP_DIR)

        # Ensure the temporary directory exists
        os.makedirs(TMP_DIR, exist_ok=True)

        # Download and process the PDF document
        response = requests.get(data.pdf_link)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Unable to download the PDF document.")

        pdf_content = response.content
        if not pdf_content:
            raise HTTPException(status_code=400, detail="Downloaded PDF is empty.")

        # Save the downloaded PDF as a temporary file in the 'tmp' directory
        pdf_file_path = os.path.join(TMP_DIR, f"temp_selected_pub_{pdf_id}.pdf")
        try:
            with open(pdf_file_path, "wb") as pdf_file:
                pdf_file.write(pdf_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving the PDF locally: {str(e)}")

        # Process the saved PDF document
        try:
            documents = get_pdf_documents(open(pdf_file_path, "rb"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing the saved PDF: {str(e)}")

        if not documents:
            raise HTTPException(status_code=500, detail="Failed to process the PDF document.")

        # Create the index using the processed documents
        initialize_settings()
        create_index(documents, pdf_id)

        return {"message": "PDF processed and index created successfully!"}
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions so they don't get re-wrapped
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the PDF: {str(e)}")


@router.post("/reload-pdf")
async def reload_pdf(data: PDFLink):
    """Force reprocessing of a given PDF link, create a fresh index, and return success message."""
    try:
        pdf_id = data.pdf_id

        # Delete existing index if it exists
        index_name = f"pdf-index-{pdf_id}"
        if index_name in pc.list_indexes().names():
            pc.delete_index(index_name)

        # Clear the temporary cache directory before processing
        clear_cache_directory(TMP_DIR)

        # Reprocess and create a new index
        response = requests.get(data.pdf_link)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Unable to download the PDF document.")

        pdf_content = response.content
        pdf_file = BytesIO(pdf_content)
        pdf_file.name = f"temp_selected_pub_{pdf_id}.pdf"

        documents = get_pdf_documents(pdf_file)
        if not documents:
            raise HTTPException(status_code=500, detail="Failed to process the PDF document.")

        initialize_settings()
        create_index(documents, pdf_id)

        return {"message": "PDF reprocessed and index created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reprocessing the PDF: {str(e)}")

@router.post("/query")
async def query_index(data: QueryRequest):
    """
    Query the index with a question and return an answer.

    Args:
        data (QueryRequest): Contains the PDF ID, the question to be queried, and the index type.

    Returns:
        dict: A dictionary containing the answer to the question.
    """
    try:
        # Initialize global settings or configurations
        initialize_settings()
        
        # Determine the index name based on the query mode
        index_name = f"{data.index_type}-{data.pdf_id}"

        # Check if the specified index exists in Pinecone
        if index_name not in pc.list_indexes().names():
            if data.index_type == "research-notes":
                raise HTTPException(status_code=404, detail="Research notes index not found. Please save research notes first.")
            else:
                raise HTTPException(status_code=404, detail="Full document index not found for the provided PDF ID.")
        
        # Set up the vector store and storage context
        vector_store = PineconeVectorStore(index_name=index_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Load the index using the storage context
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context
        )

        # Create a query engine with specified similarity settings
        query_engine = index.as_query_engine(similarity_top_k=5, streaming=False)
        
        # Query the index with the provided question
        response = query_engine.query(data.question)

        # Extract the answer text
        answer = getattr(response, "response")

        # Return the extracted answer
        return {"answer": answer}
        
    except HTTPException as http_err:
        # Handle known HTTP exceptions separately
        raise http_err
    except Exception as e:
        # Handle unexpected exceptions with a generic message
        raise HTTPException(status_code=500, detail=f"Error querying the index: {str(e)}")

