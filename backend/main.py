from flask import Flask, request, jsonify, make_response
from werkzeug.utils import secure_filename
from flask_cors import CORS
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables from .env if present
load_dotenv('.env')

# Configuration and constants
class Config:
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx', 'zip'}
    UPLOAD_FOLDER = 'uploads'

# Read environment variables (allow boto3 to fallback to other providers if these are empty)
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY") or None
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY") or None
REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or None
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME") or None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Ensure upload folder exists locally if needed
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

def build_boto3_client(service_name):
    """
    Build a boto3 client. If AWS_ACCESS_KEY / AWS_SECRET_KEY are provided,
    use them, otherwise let boto3 fall back to the normal credential chain
    (environment, shared credentials, or IAM role).
    """
    params = {}
    if REGION:
        params['region_name'] = REGION
    if AWS_ACCESS_KEY and AWS_SECRET_KEY:
        params['aws_access_key_id'] = AWS_ACCESS_KEY
        params['aws_secret_access_key'] = AWS_SECRET_KEY

    return boto3.client(service_name, **params)

# Lazy clients (constructed on demand)
def get_s3_client():
    return build_boto3_client('s3')

def get_rekognition_client():
    return build_boto3_client('rekognition')

def validate_environment():
    # Validate required environment variables for running the service (non-strict: allow IAM roles)
    missing = []
    if not BUCKET_NAME:
        missing.append('AWS_BUCKET_NAME')
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
    logger.info("Required environment variables present")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_s3_key(filename):
    timestamp = datetime.utcnow().strftime("%Y/%m/%d")
    secure_name = secure_filename(filename)
    unique_id = datetime.utcnow().strftime("%H%M%S%f")
    name_without_ext, ext = os.path.splitext(secure_name)
    unique_filename = f"{name_without_ext}_{unique_id}{ext}"
    return f"uploads/{timestamp}/{unique_filename}"

def _build_cors_preflight_response():
    resp = make_response(jsonify({'message': 'CORS preflight OK'}), 200)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return resp

def _corsify_actual_response(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

def handle_s3_error(e):
    """
    Return (body, status_code) based on boto3 ClientError.
    """
    try:
        error = e.response.get('Error', {})
        error_code = error.get('Code', '')
    except Exception:
        error_code = ''

    if error_code == 'NoSuchBucket':
        return jsonify({'error': 'Bucket does not exist'}), 400
    elif error_code == 'AccessDenied':
        return jsonify({'error': 'Access denied to S3 bucket'}), 403
    elif error_code in ('InvalidAccessKeyId', 'InvalidClientTokenId'):
        return jsonify({'error': 'Invalid AWS access key or token'}), 403
    elif error_code == 'SignatureDoesNotMatch':
        return jsonify({'error': 'Invalid AWS secret key or signature'}), 403
    else:
        # include minimal error message but avoid leaking credentials
        logger.error("S3 ClientError: %s", str(e))
        return jsonify({'error': 'S3 operation failed', 'detail': str(error.get('Message', ''))}), 500

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    if 'file' not in request.files:
        resp = jsonify({'error': 'No file part'})
        return _corsify_actual_response(make_response(resp, 400))

    file = request.files['file']

    if file.filename == '':
        resp = jsonify({'error': 'No file selected'})
        return _corsify_actual_response(make_response(resp, 400))

    if not allowed_file(file.filename):
        resp = jsonify({'error': f'File type not allowed. Allowed types: {", ".join(sorted(Config.ALLOWED_EXTENSIONS))}'})
        return _corsify_actual_response(make_response(resp, 400))

    s3 = get_s3_client()

    try:
        s3_key = generate_s3_key(file.filename)
        content_type = file.content_type or 'application/octet-stream'

        # Upload object
        s3.upload_fileobj(
            Fileobj=file,
            Bucket=BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'private'
            }
        )

        # presigned URL
        file_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )

        # Run Rekognition for image files, if available
        image_labels = None
        if content_type.startswith('image/'):
            try:
                rekognition = get_rekognition_client()
                rekog_resp = rekognition.detect_labels(
                    Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_key}},
                    MaxLabels=10,
                    MinConfidence=60
                )
                image_labels = [{'Name': l.get('Name'), 'Confidence': l.get('Confidence')} for l in rekog_resp.get('Labels', [])]
            except ClientError as e:
                logger.warning("Rekognition client error: %s", str(e))
                image_labels = []
            except Exception as e:
                logger.warning("Unexpected Rekognition error: %s", str(e))
                image_labels = []

        resp_payload = {
            'message': 'File uploaded successfully',
            'url': file_url,
            'key': s3_key,
            'filename': secure_filename(file.filename),
            'content_type': content_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        if image_labels is not None:
            resp_payload['labels'] = image_labels

        resp = jsonify(resp_payload)
        return _corsify_actual_response(make_response(resp, 200))

    except NoCredentialsError:
        logger.error("AWS credentials not available")
        resp = jsonify({'error': 'AWS credentials not available'})
        return _corsify_actual_response(make_response(resp, 500))
    except ClientError as e:
        body, status = handle_s3_error(e)
        return _corsify_actual_response(make_response(body, status))
    except Exception as e:
        logger.exception("Upload failed:")
        resp = jsonify({'error': 'File upload failed', 'detail': str(e)})
        return _corsify_actual_response(make_response(resp, 500))

@app.route('/files', methods=['GET', 'OPTIONS'])
def list_files():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    s3 = get_s3_client()

    try:
        prefix = request.args.get('prefix', 'uploads/')
        max_keys = min(int(request.args.get('limit', 100)), 1000)

        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix, MaxKeys=max_keys)

        files = []
        for obj in response.get('Contents', []):
            key = obj.get('Key')
            try:
                url = s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET_NAME, 'Key': key}, ExpiresIn=3600)
            except Exception:
                url = None
            files.append({
                'key': key,
                'size': obj.get('Size'),
                'last_modified': obj.get('LastModified').isoformat() if obj.get('LastModified') else None,
                'url': url
            })

        resp = jsonify({
            'files': files,
            'count': len(files),
            'prefix': prefix
        })
        return _corsify_actual_response(make_response(resp, 200))

    except ClientError as e:
        body, status = handle_s3_error(e)
        return _corsify_actual_response(make_response(body, status))
    except Exception as e:
        logger.exception("List files failed:")
        resp = jsonify({'error': 'Failed to list files', 'detail': str(e)})
        return _corsify_actual_response(make_response(resp, 500))

@app.route('/files/<path:key>', methods=['GET', 'OPTIONS'])
def get_file_info(key):
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    s3 = get_s3_client()

    try:
        response = s3.head_object(Bucket=BUCKET_NAME, Key=key)
        try:
            url = s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET_NAME, 'Key': key}, ExpiresIn=3600)
        except Exception:
            url = None

        file_info = {
            'key': key,
            'size': response.get('ContentLength'),
            'content_type': response.get('ContentType'),
            'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
            'url': url
        }
        resp = jsonify(file_info)
        return _corsify_actual_response(make_response(resp, 200))

    except ClientError as e:
        body, status = handle_s3_error(e)
        return _corsify_actual_response(make_response(body, status))
    except Exception as e:
        logger.exception("Get file info failed:")
        resp = jsonify({'error': 'Failed to get file info', 'detail': str(e)})
        return _corsify_actual_response(make_response(resp, 500))

@app.route('/files/<path:key>', methods=['DELETE', 'OPTIONS'])
def delete_file(key):
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    s3 = get_s3_client()

    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        logger.info("File deleted: %s", key)
        resp = jsonify({'message': 'File deleted successfully', 'key': key})
        return _corsify_actual_response(make_response(resp, 200))
    except ClientError as e:
        body, status = handle_s3_error(e)
        return _corsify_actual_response(make_response(body, status))
    except Exception as e:
        logger.exception("Delete failed:")
        resp = jsonify({'error': 'Delete failed', 'detail': str(e)})
        return _corsify_actual_response(make_response(resp, 500))

@app.route('/health', methods=['GET'])
def health_check():
    s3 = get_s3_client()
    try:
        # minimal S3 check
        s3.head_bucket(Bucket=BUCKET_NAME)
        resp = jsonify({
            'status': 'Healthy',
            'service': 'S3 File Upload API',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            's3_connection': 'OK',
            'bucket': BUCKET_NAME
        })
        return _corsify_actual_response(make_response(resp, 200))
    except Exception as e:
        logger.exception("Health check failed:")
        resp = jsonify({
            'status': 'Unhealthy',
            'service': 'S3 File Upload API',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            's3_connection': 'FAILED',
            'error': str(e)
        })
        return _corsify_actual_response(make_response(resp, 503))

@app.route('/config', methods=['GET'])
def get_config():
    resp = jsonify({
        'allowed_extensions': sorted(list(Config.ALLOWED_EXTENSIONS)),
        'max_file_size': app.config['MAX_CONTENT_LENGTH'],
        'bucket_name': BUCKET_NAME,
        'region': REGION
    })
    return _corsify_actual_response(make_response(resp, 200))

@app.errorhandler(413)
def too_large(e):
    resp = jsonify({'error': f'File too large. Maximum size is {app.config["MAX_CONTENT_LENGTH"]} bytes'})
    return _corsify_actual_response(make_response(resp, 413))

@app.errorhandler(404)
def not_found(e):
    resp = jsonify({'error': 'Endpoint not found'})
    return _corsify_actual_response(make_response(resp, 404))

@app.errorhandler(500)
def internal_error(e):
    resp = jsonify({'error': 'Internal server error'})
    return _corsify_actual_response(make_response(resp, 500))

if __name__ == "__main__":
    try:
        validate_environment()
        debug_mode = os.getenv('FLASK_ENV') == 'development'
        port = int(os.getenv('PORT', 5000))
        logger.info("Starting Flask server on port %s (debug=%s)", port, debug_mode)
        logger.info("S3 Bucket: %s, Region: %s", BUCKET_NAME, REGION)
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    except EnvironmentError as e:
        logger.error("Startup failed: %s", str(e))
    except Exception as e:
        logger.exception("Unexpected startup error:")