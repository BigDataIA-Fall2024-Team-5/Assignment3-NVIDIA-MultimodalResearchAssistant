# routers/s3_router.py

from fastapi import APIRouter, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os

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

@router.get("/fetch-image/{file_key:path}")  # Notice the ':path' type for capturing full paths
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
            # If the error code is 404, it means the object does not exist
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
    Fetch a pre-signed URL for a summary text file from S3 using the file key.
    """
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")

        # Construct the key correctly based on the folder structure in S3
        # Here, file_key should already include the entire key including folders (e.g., silver/publications/beyond-active-and-passive/beyond-active-and-passive.txt)
        try:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                raise HTTPException(status_code=404, detail="Summary file not found in S3 bucket")
            else:
                raise HTTPException(status_code=500, detail="Error checking summary file existence")

        # Generate a pre-signed URL to access the summary file if it exists
        summary_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=3600  # URL expiration time in seconds
        )
        return {"summary_url": summary_url}
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="Credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")

