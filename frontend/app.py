#app.py
import streamlit as st
from streamlit_pages import grid_view, detail_view, qa_interface

# FastAPI URL (change it if you deploy it to an online server)
API_BASE_URL = "http://localhost:8000"

def main():
    # Only show the title on the grid view page
    if st.session_state.get("page") == "grid_view":
        st.title("📚 Document Exploration Platform")

    # Initialize session state for navigation
    if "page" not in st.session_state:
        st.session_state["page"] = "grid_view"

    # Navigation between pages based on session state
    if st.session_state["page"] == "grid_view":
        grid_view.show_grid_view(API_BASE_URL)
    elif st.session_state["page"] == "detail_view":
        detail_view.show_detail_view(API_BASE_URL)
    elif st.session_state["page"] == "qa_interface":
        qa_interface.show_qa_interface(API_BASE_URL)

if __name__ == "__main__":
    main()
