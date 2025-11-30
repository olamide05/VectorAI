import boto3
import logging
from botocore.config import Config as BotoConfig
from functools import lru_cache
from config import REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY

logger = logging.getLogger(__name__)

# Standard Retry Configuration
# If AWS throttles us or a packet drops, try 3 times automatically.
retry_config = BotoConfig(
    retries={
        'max_attempts': 3,
        'mode': 'standard'
    }
)

def build_boto3_client(service_name: str):
    """
    Builds a boto3 client with automatic retry logic.
    """
    params = {
        'service_name': service_name,
        'config': retry_config
    }

    if REGION:
        params['region_name'] = REGION

    # Only pass explicit keys if they exist, otherwise rely on IAM Roles/Env vars
    if AWS_ACCESS_KEY and AWS_SECRET_KEY:
        params['aws_access_key_id'] = AWS_ACCESS_KEY
        params['aws_secret_access_key'] = AWS_SECRET_KEY

    return boto3.client(**params)

@lru_cache(maxsize=None)
def get_s3_client():
    return build_boto3_client('s3')

@lru_cache(maxsize=None)
def get_rekognition_client():
    return build_boto3_client('rekognition')