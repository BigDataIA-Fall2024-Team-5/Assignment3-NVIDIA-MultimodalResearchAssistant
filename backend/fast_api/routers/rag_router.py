from fastapi import APIRouter, UploadFile, File, HTTPException
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from utils.pdf_processor import get_pdf_documents
from pydantic import BaseModel
from typing import List
import requests
import os
import logging

router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)

# Request body models
class QueryPayload(BaseModel):
    index_id: str
    question: str

class ProcessPDFPayload(BaseModel):
    pdf_url: str

# Global storage context and vector store
STORAGE_CONTEXT = None
VECTOR_STORE = None

# Initialize settings for embedding and LLM
def initialize_settings():
    Settings.embed_model = NVIDIAEmbedding(model="nvidia/nv-embedqa-e5-v5", truncate="END")
    Settings.llm = NVIDIA(model="meta/llama-3.1-70b-instruct")
    Settings.text_splitter = SentenceSplitter(chunk_size=800)  # Increased chunk size

# Initialize global storage context
def initialize_storage_context():
    global STORAGE_CONTEXT, VECTOR_STORE
    VECTOR_STORE = MilvusVectorStore(uri="./milvus_demo.db", dim=1024, overwrite=True)
    STORAGE_CONTEXT = StorageContext.from_defaults(vector_store=VECTOR_STORE)

# Endpoint to process and index a PDF from a URL
@router.on_event("startup")
def startup_event():
    initialize_settings()
    initialize_storage_context()

@router.post("/process-pdf")
async def process_pdf(payload: ProcessPDFPayload):
    try:
        logging.info("Downloading PDF file...")
        # Download the PDF file from the provided URL
        response = requests.get(payload.pdf_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download PDF from the provided URL.")
        
        # Save the downloaded PDF temporarily
        temp_pdf_path = os.path.join("temp_files", "temp_selected_pub.pdf")
        os.makedirs("temp_files", exist_ok=True)
        
        with open(temp_pdf_path, "wb") as temp_pdf:
            temp_pdf.write(response.content)

        logging.info("Processing the downloaded PDF file...")
        # Process the PDF
        with open(temp_pdf_path, "rb") as pdf_file:
            documents = get_pdf_documents(pdf_file)

        if not documents:
            logging.error("No documents were extracted from the PDF.")
            raise HTTPException(status_code=500, detail="No documents were extracted from the PDF.")

        # Create index
        logging.info("Creating index from documents...")
        index = VectorStoreIndex.from_documents(documents, storage_context=STORAGE_CONTEXT)
        logging.info("Index created successfully with documents.")

        return {"message": "PDF processed and indexed successfully!", "index_id": "temp_index"}

    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# Endpoint to query the indexed PDF
@router.post("/query-index")
async def query_index(payload: QueryPayload):
    try:
        logging.info("Preparing to query...")
        
        # Load the index from the existing storage context
        index = VectorStoreIndex(storage_context=STORAGE_CONTEXT)

        # Validate that the index is not empty
        if not index.index_struct:
            logging.error("Index structure is missing or empty.")
            raise HTTPException(status_code=500, detail="Index structure is missing or empty.")

        # Create the query engine
        query_engine = index.as_query_engine(similarity_top_k=20, streaming=True)
        response = query_engine.query(payload.question)

        if not response or not response.response_gen:
            logging.error("No response generated for the query.")
            raise HTTPException(status_code=500, detail="No response generated for the query.")

        # Combine the response tokens into the full response
        full_response = "".join([token for token in response.response_gen])
        logging.info("Query executed successfully.")

        return {"answer": full_response}

    except Exception as e:
        logging.error(f"Error querying index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying index: {str(e)}")
