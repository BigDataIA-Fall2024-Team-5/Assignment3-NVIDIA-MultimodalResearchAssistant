from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import boto3
import fitz  # PyMuPDF
import os


# Initialize the S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)

# S3 bucket configuration
bucket_name = os.getenv('S3_BUCKET_NAME')
input_prefix = 'raw/publications/'
output_prefix = 'silver/publications/'

# Define function to list PDFs in S3
def list_pdfs_in_s3_folder(prefix):
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    pdf_files = [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.pdf')]
    return pdf_files

# Function to process PDFs and upload text and images to S3
def pymupdf_process_and_upload():
    # List all PDFs in the input folder
    pdf_files = list_pdfs_in_s3_folder(input_prefix)
    
    # Initialize a counter for processed files
    processed_count = 0

    for pdf_key in pdf_files:
        try:
            # Download the PDF file
            pdf_obj = s3.get_object(Bucket=bucket_name, Key=pdf_key)
            pdf_content = pdf_obj['Body'].read()

            # Process the PDF with PyMuPDF to extract text and images
            doc = fitz.open("pdf", pdf_content)  # Corrected line to handle byte content
            text_content = ''
            image_counter = 0

            # Create a directory for each processed PDF (remove '.pdf' extension)
            output_folder = os.path.basename(pdf_key).replace('.pdf', '')
            output_folder_key = f'{output_prefix}{output_folder}/'

            # Iterate over pages to extract text and images
            for page_num, page in enumerate(doc):
                text_content += page.get_text()

                # Extract images (potentially including graphs)
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image['image']
                    img_extension = base_image['ext']

                    # Construct image filename
                    image_filename = f'page_{page_num + 1}_image_{img_index + 1}.{img_extension}'
                    image_key = f'{output_folder_key}{image_filename}'

                    # Upload image to S3
                    s3.put_object(Bucket=bucket_name, Key=image_key, Body=img_bytes)
                    
                    # Add image reference to the text content
                    text_content += f'\n[Image: {image_filename}]\n'
                    image_counter += 1

            # Define the output filename for the extracted text with .txt extension
            output_txt_key = f'{output_folder_key}{output_folder}.txt'

            # Upload the processed text to S3
            s3.put_object(Bucket=bucket_name, Key=output_txt_key, Body=text_content.encode('utf-8'))
            print(f"Processed and uploaded: {output_txt_key} with {image_counter} images/graphs")
            
            # Increment the counter
            processed_count += 1

        except Exception as e:
            print(f"Error processing {pdf_key}: {str(e)}")

    # Print the total count of processed files
    print(f"Total PDF files processed and uploaded: {processed_count}")

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Instantiate the DAG
with DAG(
    'pdf_text_image_extraction_pipeline',
    default_args=default_args,
    description='Extract text and images from PDFs using PyMuPDF and store them in S3',
    schedule_interval=None, 
    start_date=datetime(2024, 10, 24),
    catchup=False,
) as dag:

    # Define PythonOperator
    pymupdf_extraction_task = PythonOperator(
        task_id='pymupdf_extraction_task',
        python_callable=pymupdf_process_and_upload,
    )

    # Set task dependencies (if there are more tasks, you can define them here)
    pymupdf_extraction_task
