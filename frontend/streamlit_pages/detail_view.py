import streamlit as st
import requests
from streamlit_pages.utils import fetch_image_url, fetch_pdf_url, fetch_summary  # New function to fetch summary

def show_detail_view(API_BASE_URL):
    """Displays detailed information of a selected publication."""
    if st.session_state.get("selected_pub") is not None:
        selected_pub = st.session_state["selected_pub"]

        # Create two columns: one for the image and another for text details
        col1, col2 = st.columns([1, 2])  # Adjust the proportion as needed

        with col1:
            # Display the cover image if available
            if selected_pub.get('IMAGE_LINK'):
                file_key = "/".join(selected_pub['IMAGE_LINK'].split('/')[-3:])
                image_url = fetch_image_url(API_BASE_URL, file_key)

                if image_url:
                    st.image(image_url, caption=selected_pub['TITLE'], use_column_width=True)

        with col2:
            # Display publication details with proper formatting
            st.markdown(f"### {selected_pub['TITLE']}")  # Title as a heading
            st.write(f"**Author:** {selected_pub['AUTHOR']}")
            st.write(f"**Date:** {selected_pub['DATE']}")
            st.write(f"**Description:** {selected_pub['BRIEF_SUMMARY']}")

        st.markdown("---")

        # Fetch and display the pre-signed URL for downloading the PDF
        if selected_pub.get('PDF_LINK'):
            pdf_key = "/".join(selected_pub['PDF_LINK'].split('/')[-3:])  # Extract the key from the link
            pdf_url = fetch_pdf_url(API_BASE_URL, pdf_key)  # Fetch the pre-signed URL for the PDF

            if pdf_url:
                st.markdown(f"[📄 Download PDF]({pdf_url})", unsafe_allow_html=True)

        st.markdown("---")

        # Section for additional summary information
        st.markdown("## Summary Section")
        
        # Extract the base file name without the extension from the PDF link to form the summary key
        try:
            # Get the file name without extension to use as the folder name
            base_file_name = selected_pub["PDF_LINK"].split('/')[-1].replace('.pdf', '')
            if not base_file_name:  # If the extraction fails or results in an empty string
                raise ValueError("Failed to extract folder name from the PDF link.")
                
            # Construct the summary key for `silver/publication_summary/`
            summary_key = f"silver/publication_summary/{base_file_name}.txt"
        except Exception as e:
            st.error(f"Error forming summary key: {str(e)}")
            return

        # Fetch the existing summary
        summary_content, summary_timestamp = fetch_summary(API_BASE_URL, summary_key)

        if summary_content == "generate":
            st.warning("Summary not found. Click 'Refresh' to generate one.")
        elif summary_content:
            st.write(f"*Generated on: {summary_timestamp}*")
            st.write(summary_content)
        else:
            st.warning("Summary not available. Click 'Refresh' to generate one.")

        # Add a Refresh button for summary generation
        if st.button("🔄 Refresh Summary"):
            with st.spinner("Generating summary..."):
                payload = {"pdf_link": selected_pub["PDF_LINK"]}
                response = requests.post(
                    f"{API_BASE_URL}/summarization/generate-summary",
                    json=payload
                )
                if response.status_code == 200:
                    new_summary = response.json().get("summary", "")
                    if new_summary:
                        st.success("Summary generated successfully!")
                        # Display the new summary
                        st.write(new_summary)
                    else:
                        st.warning("Summary generated but no content received.")
                else:
                    st.error(f"Failed to generate the summary. Error: {response.status_code} - {response.json().get('detail', 'Unknown error')}")

        st.markdown("---")

        # Add a button to go back to the list view
        if st.button("🔙 Back to List"):
            st.session_state["selected_pub"] = None
            st.session_state["page"] = "grid_view"
            st.rerun()
    else:
        st.error("No publication selected.")
