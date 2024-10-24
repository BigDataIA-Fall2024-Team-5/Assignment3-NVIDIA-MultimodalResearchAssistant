# app.py

import streamlit as st
from streamlit_pages import grid_view, detail_view

# FastAPI URL (change it if you deploy it to an online server)
API_BASE_URL = "http://localhost:8000"

def main():
    st.title("📚 Document Exploration Platform")

    # Initialize session state for navigation
    if "page" not in st.session_state:
        st.session_state["page"] = "grid_view"

    # Navigation between pages based on session state
    if st.session_state["page"] == "grid_view":
        grid_view.show_grid_view(API_BASE_URL)
    elif st.session_state["page"] == "detail_view":
        detail_view.show_detail_view(API_BASE_URL)

if __name__ == "__main__":
    main()
