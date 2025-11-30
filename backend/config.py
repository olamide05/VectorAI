import os
from typing import Set
from dotenv import load_dotenv

load_dotenv('.env')

class Config:
    # 15MB limit
    MAX_CONTENT_LENGTH: int = 15 * 1024 * 1024
    ALLOWED_EXTENSIONS: Set[str] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx', 'zip'}

    # AWS Settings
    REKOGNITION_MAX_LABELS: int = 10
    REKOGNITION_MIN_CONFIDENCE: int = 60
    PRESIGNED_EXPIRES: int = 3600

    # CORS (Allow specific origins in production)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# AWS Credentials
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Validation
if not BUCKET_NAME:
    # We log a warning instead of crashing to allow testing /health endpoints
    print("WARNING: AWS_BUCKET_NAME is not set. Uploads will fail.")