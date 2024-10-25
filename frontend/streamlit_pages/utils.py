import requests
import streamlit as st
from datetime import datetime
import pytz


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
        # Request to the backend to fetch the pre-signed URL and last modified time for the summary file
        response = requests.get(f"{API_BASE_URL}/s3/fetch-summary/{summary_key}")
        
        if response.status_code == 200:
            # Extract the pre-signed URL and last modified time from the backend response
            summary_url = response.json().get("summary_url")
            last_modified = response.json().get("last_modified", None)

            if summary_url:
                # Fetch the actual content of the summary using the pre-signed URL
                summary_response = requests.get(summary_url)
                
                if summary_response.status_code == 200:
                    # Convert the response content to text, assuming it's a plain text summary
                    summary_content = summary_response.text
                    
                    # If there is a last modified time, convert it to the target timezone
                    if last_modified:
                        # Parse the UTC time
                        utc_time = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%fZ")
                        # Convert to target timezone (e.g., America/New_York for UTC-04:00)
                        target_timezone = pytz.timezone("America/New_York")  # Change to your desired timezone
                        last_modified_local = utc_time.replace(tzinfo=pytz.utc).astimezone(target_timezone)
                        # Format the local time
                        last_modified = last_modified_local.strftime("%B %d, %Y, %H:%M:%S %p (%Z)")
                    
                    return summary_content, last_modified
                else:
                    return None, None  # Return None without logging error messages
            else:
                return None, None  # Return None if the pre-signed URL is not found
        elif response.status_code == 404:
            # If a 404 error is returned, the summary file does not exist
            return "generate", None  # Indicate that a new summary needs to be generated
        else:
            return None, None  # Return None without logging error messages
    except requests.exceptions.RequestException as e:
        return None, None  # Return None without logging error messages
    except Exception as e:
        return None, None  # Return None without logging error messages
