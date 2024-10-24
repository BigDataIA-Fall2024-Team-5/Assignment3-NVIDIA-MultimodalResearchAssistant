import streamlit as st
import requests

# Set up your FastAPI URL
api_url = "http://127.0.0.1:8000/api/documents"  # Update the URL if different

# Fetch documents from the FastAPI endpoint
response = requests.get(api_url)

if response.status_code == 200:
    documents = response.json().get("documents", [])
    for doc in documents:
        # Displaying each document's details
        st.subheader(doc['title'])
        st.write(f"**Summary:** {doc['summary']}")
        st.write(f"**Date:** {doc['date']}")
        st.write(f"**Author:** {doc['author']}")

        # Display the image if the link is available and valid
        if doc['image_link']:
            # Output the image URL for debugging purposes
            st.write(f"Image URL: {doc['image_link']}")

            if doc['image_link'].startswith("http"):  # Ensure it is a valid URL
                st.image(doc['image_link'], caption=doc['title'], use_column_width=True)
            else:
                st.write("Invalid image URL.")
        else:
            st.write("No image available.")

        # Provide a link to download the associated PDF
        if doc['pdf_link'] and doc['pdf_link'].startswith("http"):
            st.markdown(f"[Download PDF]({doc['pdf_link']})", unsafe_allow_html=True)
        else:
            st.write("No PDF available.")
else:
    st.error("Failed to fetch documents. Please check the API endpoint.")
