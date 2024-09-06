import boto3
import uuid
import time
import os

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    's3',
    region_name='eu-west-3',  # Replace with your AWS region
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

bucket_name = 's16-decks'

textract_client = boto3.client(
    'textract',
    region_name='eu-west-3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# print("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
# print("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY)
# Function to check job status
def check_job_status(client, job_id):
    while True:
        response = client.get_document_text_detection(JobId=job_id)
        print(response)
        status = response['JobStatus']
        if status != "IN_PROGRESS":
            return status, response
        print(f"Job {job_id} is still processing...")
        time.sleep(5)  # Wait before checking again
    
def extract_text_from_doc(pdf_buffer):
    object_name = f"{uuid.uuid4()}.pdf"
    # store object in s3
    s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=pdf_buffer)

    # Start the asynchronous text detection
    response = textract_client.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_name
            }
        }
    )

    # Extract the Job ID
    job_id = response['JobId']

    # Check the status of the job
    status, response = check_job_status(textract_client, job_id)
    
    text = ""
    if status == 'SUCCEEDED':
        text = ""
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text += block['Text'] + "\n"
        return text
    else:
        raise Exception(f"Textract job failed: {status}")

with open("testdoc.pdf", "rb") as pdf:
    text = extract_text_from_doc(pdf.read())
    print(text)