from fastapi import APIRouter, HTTPException
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from utils.pdf_processor import get_pdf_documents
from pydantic import BaseModel
import requests
import os
import logging
from pinecone import Pinecone
import hashlib
from pinecone import ServerlessSpec

router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)

# Request body models
class QueryPayload(BaseModel):
    pdf_id: str
    question: str

class ProcessPDFPayload(BaseModel):
    pdf_url: str

# Initialize Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

# Initialize settings for embedding and LLM
def initialize_settings():
    Settings.embed_model = NVIDIAEmbedding(model="nvidia/nv-embedqa-e5-v5", truncate="END")
    Settings.llm = NVIDIA(model="meta/llama-3.1-70b-instruct")
    Settings.text_splitter = SentenceSplitter(chunk_size=800)  # Increased chunk size

@router.on_event("startup")
def startup_event():
    initialize_settings()

@router.post("/process-pdf")
async def process_pdf(payload: ProcessPDFPayload):
    try:
        logging.info("Downloading PDF file...")
        response = requests.get(payload.pdf_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download PDF from the provided URL.")
        
        pdf_content = response.content
        pdf_id = hashlib.md5(payload.pdf_url.encode()).hexdigest()

        logging.info("Processing the downloaded PDF file...")
        documents = get_pdf_documents(pdf_content)

        if not documents:
            logging.error("No documents were extracted from the PDF.")
            raise HTTPException(status_code=500, detail="No documents were extracted from the PDF.")

        # Create index
        index_name = f"pdf-index-{pdf_id}"[:62]  # Ensure the name is not too long
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name=index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"  # GCP region for free tier
                )
            )

        vector_store = PineconeVectorStore(index_name=index_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        logging.info("Creating index from documents...")
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        logging.info("Index created successfully with documents.")

        return {"message": "PDF processed and indexed successfully!", "pdf_id": pdf_id}

    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.post("/query-index")
async def query_index(payload: QueryPayload):
    try:
        logging.info("Preparing to query...")
        
        index_name = f"pdf_index_{payload.pdf_id}"
        vector_store = PineconeVectorStore(index_name=index_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_vector_store(vector_store)

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

