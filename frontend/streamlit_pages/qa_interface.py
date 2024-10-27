import re
from pinecone import Pinecone
import os
import requests
import streamlit as st
from io import BytesIO
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from utils.pdf_processor import get_pdf_documents
from utils.helper_functions import set_environment_variables
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import ServerlessSpec
import hashlib

# Initialize environment variables
set_environment_variables()

# Initialize Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

# Initialize settings
def initialize_settings():
    Settings.embed_model = NVIDIAEmbedding(model="nvidia/nv-embedqa-e5-v5", truncate="END")
    Settings.llm = NVIDIA(model="meta/llama-3.1-70b-instruct")
    Settings.text_splitter = SentenceSplitter(chunk_size=650)

# Create index from documents
def create_index(documents, pdf_id):
    index_name = f"pdf-index-{re.sub(r'[^a-z0-9-]', '-', pdf_id.lower())}"
    index_name = re.sub(r'^[^a-z]', 'a', index_name)  # Ensure it starts with a letter
    index_name = index_name[:62]  # Limit to 62 characters (Pinecone's limit is 63)
    
    # Check if the index already exists, if not, create it
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
    # Initialize the Pinecone vector store
    vector_store = PineconeVectorStore(index_name=index_name)
    
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_documents(documents, storage_context=storage_context)

# Main function to run the Streamlit app
def show_qa_interface():
    """Displays the Q/A interface for the selected publication."""
    st.write(f"Debug: Selected PDF URL is {st.session_state.get('selected_pdf_url', 'Not Set')}")
    # Initialize settings for embeddings and LLM
    initialize_settings()

    if "selected_pdf_url" not in st.session_state or not st.session_state["selected_pdf_url"]:
        st.error("No PDF selected. Please go back and select a publication first.")
        return

    selected_pdf_url = st.session_state["selected_pdf_url"]

    # Validate URL
    if not selected_pdf_url.startswith(('http://', 'https://')):
        st.error(f"Invalid URL: {selected_pdf_url}")
        return

    # Generate a unique pdf_id
    pdf_id = hashlib.md5(selected_pdf_url.encode()).hexdigest()


    st.title("Q/A Interface")


    # Add a button to go back to the detail view at the top
    if st.button("🔙 Back to Detail View"):
        st.session_state["page"] = "detail_view"
        st.rerun()

    # Display the selected PDF link for reference
    st.markdown(f"[📄 View Selected PDF]({selected_pdf_url})", unsafe_allow_html=True)

    # Step 1: Download, process, and index the PDF, only if not already processed
    if "index" not in st.session_state:
        with st.spinner("Downloading, processing, and indexing PDF..."):
            try:
                response = requests.get(selected_pdf_url)
                if response.status_code == 200:
                    pdf_content = response.content
                    pdf_file = BytesIO(pdf_content)
                    pdf_file.name = f"temp_selected_pub_{pdf_id}.pdf"

                    # Process the downloaded PDF
                    documents = get_pdf_documents(pdf_file)

                    if not documents:
                        st.error("Failed to process the PDF.")
                        return

                    # Create index and store it in session state
                    st.session_state['index'] = create_index(documents, pdf_id)
                    st.session_state['history'] = []
                    st.success("PDF processed and index created!")

                else:
                    st.error("Failed to download the PDF.")
                    return
            except Exception as e:
                st.error(f"Error downloading and processing the PDF: {str(e)}")
                return

    # Step 2: Display chat for Q/A
    st.markdown("## Chat with the Assistant")

    if 'index' in st.session_state:
        if 'history' not in st.session_state:
            st.session_state['history'] = []

        query_engine = st.session_state['index'].as_query_engine(similarity_top_k=20, streaming=True)

        user_input = st.chat_input("Enter your query:")

        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state['history']:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state['history'].append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                # Send the query to the local processing engine for answering
                try:
                    response = query_engine.query(user_input)
                    for token in response.response_gen:
                        full_response += token
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                except Exception as e:
                    st.error(f"Error querying the assistant: {str(e)}")

            st.session_state['history'].append({"role": "assistant", "content": full_response})

        # Add a clear button
        if st.button("Clear Chat"):
            st.session_state['history'] = []
            st.rerun()

    st.markdown("---")

if __name__ == "__main__":
    show_qa_interface()