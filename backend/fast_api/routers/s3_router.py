# routers/s3_router.py

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

router = APIRouter(
    prefix="/s3",
    tags=["S3"]
)

# Initialize S3 client using environment variables
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

class FetchNotesRequest(BaseModel):
    pdf_link: str

class SaveNotesRequest(BaseModel):
    pdf_link: str
    notes: str

@router.get("/fetch-image/{file_key:path}")
async def fetch_image_from_s3(file_key: str):
    """
    Fetch an image from S3 using the file key.
    """
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")
        print(f"Received request for file_key: {file_key}")  # Debugging line

        # Check if the file exists in S3 by trying to get its metadata
        try:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                raise HTTPException(status_code=404, detail="File not found in S3 bucket")
            else:
                raise HTTPException(status_code=500, detail="Error checking file existence")

        # Generate a pre-signed URL to access the image if it exists
        image_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=3600  # URL expiration time in seconds
        )
        return {"image_url": image_url}
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="Credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")

@router.get("/fetch-pdf/{file_key:path}")
async def fetch_pdf_from_s3(file_key: str):
    """
    Fetch a pre-signed URL for a PDF from S3 using the file key.
    """
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")

        # Check if the file exists in S3 by trying to get its metadata
        try:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                raise HTTPException(status_code=404, detail="PDF file not found in S3 bucket")
            else:
                raise HTTPException(status_code=500, detail="Error checking PDF file existence")

        # Generate a pre-signed URL to access the PDF if it exists
        pdf_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=3600  # URL expiration time in seconds
        )
        return {"pdf_url": pdf_url}
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="Credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PDF: {str(e)}")
    
@router.get("/fetch-summary/{file_key:path}")
async def fetch_summary_from_s3(file_key: str):
    """
    Fetch a pre-signed URL for a summary text file from S3 using the file key, and return the last modified timestamp.
    """
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")

        # Check if the file exists in S3 by trying to get its metadata and last modified timestamp
        try:
            head_response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                raise HTTPException(status_code=404, detail="Summary file not found in S3 bucket")
            else:
                raise HTTPException(status_code=500, detail="Error checking summary file existence")

        # Extract the last modified timestamp from the response
        last_modified = head_response.get("LastModified")
        last_modified_str = last_modified.strftime("%Y-%m-%dT%H:%M:%S.%fZ") if last_modified else None

        # Generate a pre-signed URL to access the summary file if it exists
        summary_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=3600  # URL expiration time in seconds
        )
        
        return {
            "summary_url": summary_url,
            "last_modified": last_modified_str
        }

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="Credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")


@router.get("/fetch-research-notes")
async def fetch_research_notes(pdf_link: str):
    """
    Fetch research notes from S3 using the derived base file name as the file key.
    """
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")
        base_file_name = pdf_link.split('/')[-1].replace('.pdf', '').replace(' ', '-').lower()
        notes_key = f"research_notes/{base_file_name}.txt"

        # Check if the notes file exists in S3 by trying to get its metadata
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=notes_key)
            notes_content = response['Body'].read().decode('utf-8')
            return {"notes": notes_content}
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                return {"notes": ""}  # Return empty notes gracefully
            else:
                raise HTTPException(status_code=500, detail="Error fetching research notes from S3.")

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="Credentials not available.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching research notes: {str(e)}")


@router.post("/save-research-notes")
async def save_research_notes(request: SaveNotesRequest):
    """
    Save or update research notes in S3 using the derived base file name as the file key.
    """
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")
        base_file_name = request.pdf_link.split('/')[-1].replace('.pdf', '').replace(' ', '-').lower()
        notes_key = f"research_notes/{base_file_name}.txt"
        
        # Upload the notes content to S3
        s3_client.put_object(Bucket=bucket_name, Key=notes_key, Body=request.notes.encode('utf-8'))
        return {"message": "Research notes saved successfully."}

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="Credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving research notes: {str(e)}")
