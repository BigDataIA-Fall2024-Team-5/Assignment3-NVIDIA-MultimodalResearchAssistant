import requests
import streamlit as st

# Main function to run the Streamlit app
def show_qa_interface(API_BASE_URL):
    """Displays the Q/A interface for the selected publication."""
    st.write(f"Debug: Selected PDF ID is {st.session_state.get('selected_pdf_id', 'Not Set')}")

    if "selected_pdf_id" not in st.session_state or not st.session_state["selected_pdf_id"]:
        st.error("No PDF ID found. Please go back and select a publication first.")
        return

    pdf_id = str(st.session_state["selected_pdf_id"])

    st.title("Q/A Interface")

    # Add a button to go back to the detail view at the top
    if st.button("🔙 Back to Detail View"):
        st.session_state["page"] = "detail_view"
        st.rerun()

    # Display the selected PDF link for reference
    selected_pdf_url = st.session_state.get("selected_pdf_url", "")
    if selected_pdf_url:
        st.markdown(f"[📄 View Selected PDF]({selected_pdf_url})", unsafe_allow_html=True)

    # Step 1: Check if the index exists, otherwise process and index the PDF
    if "current_pdf_id" not in st.session_state or st.session_state["current_pdf_id"] != pdf_id:
        st.session_state["current_pdf_id"] = pdf_id
        st.session_state["index"] = False

    if not st.session_state["index"]:
        with st.spinner("Checking if index already exists..."):
            try:
                response = requests.get(f"{API_BASE_URL}/rag/check-index", params={"pdf_id": pdf_id})
                if response.status_code == 200 and response.json().get("index_exists"):
                    st.session_state['index'] = True
                    st.session_state['history'] = []
                    st.success("Index already exists! You can start querying.")
                else:
                    with st.spinner("Processing and indexing PDF..."):
                        response = requests.post(f"{API_BASE_URL}/rag/process-pdf", json={"pdf_link": selected_pdf_url, "pdf_id": pdf_id})
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
        with st.spinner("Reprocessing and reindexing PDF..."):
            try:
                response = requests.post(f"{API_BASE_URL}/rag/reload-pdf", json={"pdf_link": selected_pdf_url, "pdf_id": pdf_id})
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

    # Step 2: Display chat for Q/A
    st.markdown("## Chat with the Assistant")

    if 'index' in st.session_state:
        if 'history' not in st.session_state:
            st.session_state['history'] = []

        def query_engine(query):
            try:
                response = requests.post(f"{API_BASE_URL}/rag/query", json={"question": query, "pdf_id": pdf_id})
                if response.status_code == 200:
                    return response.json().get("answer", "")
                else:
                    return f"Error querying the assistant: {response.status_code} - {response.json().get('detail', 'Unknown error')}"
            except Exception as e:
                return f"Error querying the assistant: {str(e)}"

        user_input = st.chat_input("Enter your query:")

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
                full_response = query_engine(user_input)
                message_placeholder.markdown(full_response)

            st.session_state['history'].append({"role": "assistant", "content": full_response})

        if st.button("Clear Chat"):
            st.session_state['history'] = []
            st.rerun()

    st.markdown("---")
