# streamlit_pages/utils.py

import requests
import streamlit as st

def fetch_publications(API_BASE_URL):
    """Fetches a list of publications from the FastAPI server."""
    try:
        response = requests.get(f"{API_BASE_URL}/snowflake/publications")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch publications. Please try again later.")
            return []
    except Exception as e:
        st.error(f"Error fetching publications: {str(e)}")
        return []

def fetch_image_url(API_BASE_URL, file_key):
    """Fetches a pre-signed URL for an image from the S3 bucket using FastAPI."""
    placeholder_image_path = "no-image-placeholder.png"

    if file_key and "https://" not in file_key:
        try:
            response = requests.get(f"{API_BASE_URL}/s3/fetch-image/{file_key}")
            if response.status_code == 200:
                return response.json().get("image_url", placeholder_image_path)
            return placeholder_image_path
        except Exception:
            return placeholder_image_path
    else:
        return placeholder_image_path

def fetch_pdf_url(API_BASE_URL, file_key):
    """Fetches a pre-signed URL for a PDF from the S3 bucket using FastAPI."""
    try:
        response = requests.get(f"{API_BASE_URL}/s3/fetch-pdf/{file_key}")
        if response.status_code == 200:
            return response.json().get("pdf_url")
        return None
    except Exception as e:
        st.error(f"Error fetching PDF URL: {str(e)}")
        return None
