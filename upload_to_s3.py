import os
import boto3
from dotenv import load_dotenv


load_dotenv()

def upload_raw_data_to_s3(file_name, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_name

    object_name = f"raw/{object_name}"
    s3_client = boto3.client(
        's3', 
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'), 
        region_name = os.getenv('AWS_REGION')
    )
    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
        return True
    except Exception as e:
        print("Error during loading on AWS: {e}")
        return False

if __name__ == "__main__":
    name_bucket = "claudia-youtube-insight"
    local_file = "youtube_trending_data.json"
    upload_raw_data_to_s3(local_file, name_bucket )
    