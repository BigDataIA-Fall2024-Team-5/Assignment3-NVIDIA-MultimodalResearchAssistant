import requests
import streamlit as st

# Main function to run the Streamlit app
def show_qa_interface(API_BASE_URL):
    """Displays the Q/A interface for the selected publication."""
    
    # Initialize session state keys
    if "research_notes" not in st.session_state:
        st.session_state["research_notes"] = ""
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "index" not in st.session_state:
        st.session_state["index"] = False
    if "current_pdf_id" not in st.session_state:
        st.session_state["current_pdf_id"] = None

    selected_pub = st.session_state.get("selected_pub")
    pdf_link = selected_pub.get("PDF_LINK")
    pub_id = str(selected_pub.get("ID"))
    selected_pdf_url = st.session_state.get("selected_pdf_url", "")

    st.title("Q/A Interface")

    # Fetch or create research notes on load
    if not st.session_state.get("fetched_notes", False):
        fetch_or_create_notes(API_BASE_URL, pdf_link)
        st.session_state["fetched_notes"] = True

    # Add a button to go back to the detail view at the top
    if st.button("🔙 Back to Detail View"):
        clear_session_state()
        st.session_state["page"] = "detail_view"
        st.rerun()

    # Display the selected PDF link for reference
    if pdf_link:
        st.markdown(f"[📄 View Selected PDF]({selected_pdf_url})", unsafe_allow_html=True)

    # Step 1: Check if the index exists, otherwise process and index the PDF
    if st.session_state["current_pdf_id"] != pub_id:
        st.session_state["current_pdf_id"] = pub_id
        st.session_state["index"] = False

    if not st.session_state["index"]:
        with st.spinner("Checking if index already exists..."):
            try:
                response = requests.get(f"{API_BASE_URL}/rag/check-index", params={"pdf_id": pub_id})
                if response.status_code == 200 and response.json().get("index_exists"):
                    st.session_state['index'] = True
                    st.session_state['history'] = []
                    st.success("Index already exists! You can start querying.")
                else:
                    with st.spinner("Processing and indexing PDF..."):
                        response = requests.post(f"{API_BASE_URL}/rag/process-pdf", json={"pdf_link": selected_pdf_url, "pdf_id": pub_id})
                        if response.status_code == 200:
                            st.session_state['index'] = True
                            st.session_state['history'] = []
                            st.success("PDF processed and index created successfully!")
                        else:
                            st.error(f"Failed to process the PDF. Error: {response.status_code} - {response.json().get('detail', 'Unknown error')}")
                            return
            except Exception as e:
                st.error(f"Error during processing or index check: {str(e)}")
                return

    # Add a button to reload the Q/A interface (force reprocessing)
    if st.button("Reload Q/A Interface"):
        reload_qa_interface(API_BASE_URL, selected_pdf_url, pub_id)

    # Research Notes section
    st.markdown("## Research Notes")
    st.text_area("Research Notes", value=st.session_state.get("research_notes", ""), height=200, key="research_notes_input", on_change=update_research_notes)

    if st.button("Save Notes to S3"):
        save_notes_to_s3(API_BASE_URL, pdf_link)

    # Step 2: Display chat for Q/A
    st.markdown("## Chat with the Assistant")

    if st.session_state["index"]:
        def query_engine(query):
            try:
                response = requests.post(f"{API_BASE_URL}/rag/query", json={"question": query, "pdf_id": pub_id})
                if response.status_code == 200:
                    return response.json().get("answer", "")
                else:
                    return f"Error querying the assistant: {response.status_code} - {response.json().get('detail', 'Unknown error')}."
            except Exception as e:
                return f"Error querying the assistant: {str(e)}"

        # Display chat history with unique keys for the Save button to avoid duplicates
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state['history']):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if message["role"] == "assistant":
                        if st.button("Save to Research Notes", key=f"save_{message['role']}_{i}"):
                            append_to_research_notes(message["content"])

        # Move chat input to the bottom of the chat container
        user_input = st.chat_input("Enter your query:")
        if user_input:
            # Add user's message to chat history
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state['history'].append({"role": "user", "content": user_input})

            # Process assistant's response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = query_engine(user_input)
                message_placeholder.markdown(full_response)

            st.session_state['history'].append({"role": "assistant", "content": full_response})
            st.rerun()  # Rerun to update the Save button instantly

        if st.button("Clear Chat"):
            st.session_state['history'] = []
            st.rerun()

def clear_session_state():
    """Clears specific session state variables."""
    keys_to_clear = ["selected_pdf_id", "index", "history", "research_notes", "current_pdf_id", "fetched_notes"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def fetch_or_create_notes(API_BASE_URL, pdf_link):
    """Fetch research notes if they exist or create an empty file initially."""
    try:
        response = requests.get(f"{API_BASE_URL}/s3/fetch-research-notes", params={"pdf_link": pdf_link})
        if response.status_code == 200:
            st.session_state["research_notes"] = response.json().get("notes", "")
        else:
            st.session_state["research_notes"] = ""
    except Exception as e:
        st.error(f"Error fetching research notes: {str(e)}")

def reload_qa_interface(API_BASE_URL, selected_pdf_url, pub_id):
    """Reloads and reprocesses the Q/A interface for the given publication."""
    with st.spinner("Reprocessing and reindexing PDF..."):
        try:
            response = requests.post(f"{API_BASE_URL}/rag/reload-pdf", json={"pdf_link": selected_pdf_url, "pdf_id": pub_id})
            if response.status_code == 200:
                st.session_state['index'] = True
                st.session_state['history'] = []
                st.success("PDF reprocessed and index recreated successfully!")
            else:
                st.error(f"Failed to reload the Q/A Interface. Error: {response.status_code} - {response.json().get('detail', 'Unknown error')}")
                return
        except Exception as e:
            st.error(f"Error reloading the Q/A Interface: {str(e)}")
            return

def update_research_notes():
    """Update research notes in session state when edited."""
    st.session_state["research_notes"] = st.session_state["research_notes_input"]

def save_notes_to_s3(API_BASE_URL, pdf_link):
    """Save research notes to S3."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/s3/save-research-notes",
            json={"pdf_link": pdf_link, "notes": st.session_state["research_notes"]}
        )
        if response.status_code == 200:
            st.success("Research notes saved successfully!")
        else:
            st.error("Failed to save research notes to S3.")
    except Exception as e:
        st.error(f"Error saving research notes: {str(e)}")

def append_to_research_notes(content):
    """Append assistant's response to the research notes."""
    st.session_state["research_notes"] += f"\n\n{content}"
    st.rerun()
