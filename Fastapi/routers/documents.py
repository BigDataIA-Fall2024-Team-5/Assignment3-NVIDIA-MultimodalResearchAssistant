from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from config import get_snowflake_connection
import boto3
import logging
from urllib.parse import urlparse

router = APIRouter()

# Function to generate a pre-signed URL for S3 images
def generate_s3_presigned_url(url):
    s3_client = boto3.client(
        's3',
        aws_access_key_id='AKIA42PHHPNDY4KC46A4',
        aws_secret_access_key='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',
        region_name='us-east-2'
    )
    try:
        # Extract the S3 key (path) from the full URL
        key = urlparse(url).path.lstrip('/')
        
        if key:  # Check if the key is not empty or None
            logging.debug(f"Generating pre-signed URL for key: {key}")
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'publications-data-store', 'Key': key},
                ExpiresIn=3600  # URL valid for 1 hour
            )
            return response
        else:
            logging.warning(f"No valid key provided: {key}")
            return None
    except Exception as e:
        logging.error(f"Error generating pre-signed URL: {str(e)}")
        return None

@router.get("/documents")
async def get_documents():
    try:
        logging.debug("Fetching documents from Snowflake...")
        # Establish a connection to Snowflake
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Query to fetch document data
        fetch_query = """
        SELECT TITLE, BRIEF_SUMMARY, DATE, AUTHOR, IMAGE_LINK, PDF_LINK
        FROM PUBLICATION_LIST;
        """
        cursor.execute(fetch_query)
        records = cursor.fetchall()

        if not records:  # Check if no records were returned
            logging.error("No documents found in the database.")
            raise HTTPException(status_code=404, detail="No documents found.")

        # Convert records to a list of dictionaries
        documents = []
        for row in records:
            logging.debug(f"Processing row: {row}")

            # Safely handle each column with a fallback default if None
            title = row[0] or "Untitled"
            summary = row[1] or "No summary available"
            date = row[2] or "No date"
            author = row[3] or "Unknown author"
            image_url = row[4] if row[4] and row[4] != "NA" else None
            pdf_link = row[5] if row[5] and row[5] != "NA" else None

            # Generate the pre-signed URL for the image, if available
            if image_url:
                image_url = generate_s3_presigned_url(image_url)

            documents.append({
                "title": title,
                "summary": summary,
                "date": date,
                "author": author,
                "image_link": image_url,
                "pdf_link": pdf_link
            })

        # Close the cursor and connection
        cursor.close()
        conn.close()
        logging.debug("Documents fetched successfully.")
        
        # Return the document list as JSON
        return JSONResponse(content={"documents": documents})
    
    except Exception as e:
        logging.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")
