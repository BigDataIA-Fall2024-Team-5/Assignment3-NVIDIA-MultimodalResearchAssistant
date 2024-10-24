# streamlit_pages/detail_view.py

import streamlit as st
from streamlit_pages.utils import fetch_image_url, fetch_pdf_url  # New function to fetch PDF URL

def show_detail_view(API_BASE_URL):
    """Displays detailed information of a selected publication."""
    if st.session_state.get("selected_pub") is not None:
        selected_pub = st.session_state["selected_pub"]

        # Create two columns: one for the image and another for text details
        col1, col2 = st.columns([1, 2])  # Adjust the proportion as needed

        with col1:
            # Display the cover image if available
            if selected_pub.get('cover_image_link'):
                file_key = "/".join(selected_pub['cover_image_link'].split('/')[-3:])
                image_url = fetch_image_url(API_BASE_URL, file_key)

                if image_url:
                    st.image(image_url, caption=selected_pub['title'], use_column_width=True)

        with col2:
            # Display publication details with proper formatting
            st.markdown(f"### {selected_pub['title']}")  # Title as a heading
            st.write(f"**Author:** {selected_pub['author']}")
            st.write(f"**Date:** {selected_pub['date']}")
            st.write(f"**Description:** {selected_pub['description']}")

        st.markdown("---")

        # Fetch and display the pre-signed URL for downloading the PDF
        if selected_pub.get('pdf_link'):
            pdf_key = "/".join(selected_pub['pdf_link'].split('/')[-3:])  # Extract the key from the link
            pdf_url = fetch_pdf_url(API_BASE_URL, pdf_key)  # Fetch the pre-signed URL for the PDF

            if pdf_url:
                st.markdown(f"[📄 Download PDF]({pdf_url})", unsafe_allow_html=True)

        # Section for additional summary information (you can fill in the logic later)
        st.markdown("## Summary Section")
        st.write("This is where the summary information will be displayed. You can implement this section later.")

        st.markdown("---")

        # Add a button to go back to the list view
        if st.button("🔙 Back to List"):
            st.session_state["selected_pub"] = None
            st.session_state["page"] = "grid_view"
            st.rerun()
    else:
        st.error("No publication selected.")
