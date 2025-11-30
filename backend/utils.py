import os
import uuid
import logging
from datetime import datetime
from flask import jsonify
from werkzeug.utils import secure_filename
from config import Config

logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def generate_s3_key(filename: str) -> str:
    """
    Generate a collision-resistant S3 key.
    Format: uploads/YYYY/MM/DD/<uuid>_<sanitized_name>
    """
    timestamp = datetime.utcnow().strftime("%Y/%m/%d")
    secure_name = secure_filename(filename)
    # Using UUID4 is safer than timestamp for high-concurrency uniqueness
    unique_id = str(uuid.uuid4())[:8]

    name_without_ext, ext = os.path.splitext(secure_name)
    # Truncate filename to prevent key length issues
    name_short = name_without_ext[:50]

    unique_filename = f"{name_short}_{unique_id}{ext}"
    return f"uploads/{timestamp}/{unique_filename}"

def format_error(message: str, code: int = 400):
    return jsonify({'error': message}), code

def handle_aws_error(e, resource_name="AWS Resource"):
    """
    Parses boto3 ClientError into a clean JSON response.
    """
    logger.exception(f"{resource_name} Error: {e}")
    try:
        error_data = e.response.get('Error', {})
        code = error_data.get('Code', 'Unknown')
        msg = error_data.get('Message', 'Unknown error')
    except Exception:
        code = 'Unknown'
        msg = str(e)

    if code == 'NoSuchBucket':
        return format_error('Server misconfiguration: Bucket not found', 500)
    if code == 'AccessDenied':
        return format_error('Access Denied to storage backend', 403)
    if code in ('InvalidAccessKeyId', 'InvalidClientTokenId', 'SignatureDoesNotMatch'):
        return format_error('Invalid AWS Credentials on server', 500)
    if code == 'EntityTooLarge':
        return format_error('File exceeds AWS S3 size limits', 413)

    return format_error('Storage operation failed', 500)