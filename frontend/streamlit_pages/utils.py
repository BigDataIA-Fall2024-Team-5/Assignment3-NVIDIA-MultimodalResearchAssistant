import requests
import streamlit as st
from datetime import datetime

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

def fetch_summary(API_BASE_URL, summary_key):
    """Fetches the summary from the S3 bucket using a pre-signed URL."""
    try:
        # Request to the backend to fetch the pre-signed URL for the summary file
        response = requests.get(f"{API_BASE_URL}/s3/fetch-summary/{summary_key}")
        
        if response.status_code == 200:
            # Extract the pre-signed URL from the backend response
            summary_url = response.json().get("summary_url")
            if summary_url:
                # Fetch the actual content of the summary using the pre-signed URL
                summary_response = requests.get(summary_url)
                
                if summary_response.status_code == 200:
                    # Convert the response content to text, assuming it's a plain text summary
                    summary_content = summary_response.text
                    # Optionally, extract the timestamp from the response headers if needed
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    return summary_content, timestamp
                else:
                    st.error(f"Failed to retrieve summary content. HTTP status: {summary_response.status_code}")
                    return None, None
            else:
                st.error("Pre-signed URL for the summary not found in the response.")
                return None, None
        elif response.status_code == 500:
            # If there is a 500 error (file not found), return a signal to generate the summary
            return "generate", None
        else:
            st.error(f"Failed to fetch pre-signed URL for summary. HTTP status: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching summary: {str(e)}")
        return None, None
    except Exception as e:
        st.error(f"Unexpected error fetching summary: {str(e)}")
        return None, None