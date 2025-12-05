import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError, ClientError

from config import Config, BUCKET_NAME
from aws_clients import get_s3_client, get_rekognition_client
from utils import allowed_file, generate_s3_key, handle_aws_error, format_error

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return format_error('No file part', 400)

    file = request.files['file']
    if file.filename == '':
        return format_error('No file selected', 400)

    if not allowed_file(file.filename):
        return format_error(f'File type not allowed.', 400)

    # Note: We rely on Flask's MAX_CONTENT_LENGTH for size limit logic.
    s3 = get_s3_client()
    try:
        s3_key = generate_s3_key(file.filename)
        content_type = file.content_type or 'application/octet-stream'
        original_name = secure_filename(file.filename)

        # Upload with Metadata
        s3.upload_fileobj(
            Fileobj=file,
            Bucket=BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': {'original-name': original_name}
            }
        )

        # Generate URL
        file_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=Config.PRESIGNED_EXPIRES
        )

        # Initialize AI results
        image_labels = []
        detected_text = []

        # Run Rekognition (Best effort: capture error but don't fail upload)
        if content_type.startswith('image/'):
            try:
                rek = get_rekognition_client()

                # 1. Detect Labels
                rek_resp = rek.detect_labels(
                    Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_key}},
                    MaxLabels=Config.REKOGNITION_MAX_LABELS,
                    MinConfidence=Config.REKOGNITION_MIN_CONFIDENCE
                )
                image_labels = [{'Name': l['Name'], 'Confidence': l['Confidence']} for l in rek_resp.get('Labels', [])]

                # 2. Detect Text (OCR)
                text_resp = rek.detect_text(
                    Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_key}}
                )
                # Filter for full lines of text only
                detected_text = [t['DetectedText'] for t in text_resp['TextDetections'] if t['Type'] == 'LINE']

            except ClientError as e:
                logger.warning(f"Rekognition failed for {s3_key}: {e}")
            except Exception as e:
                logger.warning(f"AI processing failed silently: {e}")
                pass

        return jsonify({
            'message': 'Upload successful',
            'url': file_url,
            'key': s3_key,
            'filename': original_name,
            'labels': image_labels,
            'text': detected_text,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 201

    except NoCredentialsError:
        return format_error('AWS credentials missing', 500)
    except ClientError as e:
        return handle_aws_error(e, "S3 Upload")
    except Exception as e:
        logger.exception("Unexpected upload error")
        return format_error('Internal upload error', 500)

@api_bp.route('/files', methods=['GET'])
def list_files():
    s3 = get_s3_client()
    prefix = request.args.get('prefix', 'uploads/')
    limit = min(int(request.args.get('limit', 100)), 1000)

    try:
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix, PaginationConfig={'MaxItems': limit})

        files = []
        for page in page_iterator:
            for obj in page.get('Contents', []):
                files.append({
                    'key': obj.get('Key'),
                    'size': obj.get('Size'),
                    'last_modified': obj.get('LastModified').isoformat()
                })

        return jsonify({'files': files, 'count': len(files), 'prefix': prefix})

    except ClientError as e:
        return handle_aws_error(e, "S3 List")

@api_bp.route('/files/<path:key>', methods=['GET'])
def get_file_details(key):

    s3 = get_s3_client()
    try:
        # Check if exists
        head = s3.head_object(Bucket=BUCKET_NAME, Key=key)

        # Now we generate the URL (only when specifically asked)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key},
            ExpiresIn=Config.PRESIGNED_EXPIRES
        )

        return jsonify({
            'key': key,
            'url': url,
            'size': head.get('ContentLength'),
            'content_type': head.get('ContentType'),
            'metadata': head.get('Metadata', {}),
            'last_modified': head.get('LastModified').isoformat()
        })

    except ClientError as e:
        return handle_aws_error(e, "S3 Head")

@api_bp.route('/files/<path:key>', methods=['DELETE'])
def delete_file(key):
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        return jsonify({'message': 'File deleted', 'key': key}), 200
    except ClientError as e:
        return handle_aws_error(e, "S3 Delete")

@api_bp.route('/health', methods=['GET'])
def health_check():
    s3 = get_s3_client()
    status = {'service': 'S3 API', 'status': 'Healthy', 'timestamp': datetime.utcnow().isoformat()}

    if not BUCKET_NAME:
        status['s3_connection'] = 'Not Configured'
        return jsonify(status), 200

    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        status['s3_connection'] = 'OK'
        return jsonify(status), 200
    except Exception as e:
        status['status'] = 'Degraded'
        status['s3_connection'] = 'Unreachable'
        status['error'] = str(e)
        return jsonify(status), 503