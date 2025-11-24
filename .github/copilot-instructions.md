# VectorAI (Universal Visual Assistant) - Copilot Instructions

## Project Overview
**VectorAI** is a full-stack conversational AI application for image analysis and secure file sharing. The MVP focuses on object recognition, PDF/image uploads to AWS S3, and AI-powered chat discussions.

**Tech Stack:**
- **Backend**: Python Flask (file upload API + AI integration)
- **Frontend**: Next.js 15 with React 19, TypeScript, Tailwind CSS
- **Storage**: AWS S3 with presigned URLs (1-hour expiry)
- **Infrastructure**: Docker (multi-stage builds for production)

---

## Architecture & Data Flow

### Backend Structure (`backend/main.py`)
Flask REST API with four core responsibilities:

1. **S3 File Operations**
   - `/upload` (POST): Upload images/PDFs, generates unique S3 keys with timestamp folders (`uploads/YYYY/MM/DD/`)
   - `/files` (GET): List uploaded files with presigned URLs
   - `/files/<key>` (GET/DELETE): Retrieve or delete specific files
   
2. **Configuration & Validation**
   - File types: `png, jpg, jpeg, gif, pdf, txt, doc, docx, zip`
   - Max file size: 15MB (enforced by `MAX_CONTENT_LENGTH`)
   - S3 ACL: Always `private` - access via presigned URLs only

3. **CORS Handling**
   - Custom preflight response builder (`_build_cors_preflight_response()`)
   - Responses wrapped with CORS headers via `_corsify_actual_response()`
   - Necessary for Next.js frontend cross-origin requests

4. **Error Handling**
   - S3-specific errors mapped to HTTP status codes
   - Missing credentials, invalid keys, and access denied errors handled separately
   - Logging to stdout (important for Docker/container debugging)

### Frontend Structure (`frontend/uva/src/app/`)
Single-page app (built with Next.js App Router):

- **`layout.tsx`**: Root layout with Geist fonts, Tailwind CSS globals
- **`page.tsx`**: Main upload interface with drag-drop, file validation, progress tracking
  - Axios instance for backend calls
  - File type validation: images + PDFs only
  - Progress state management for upload feedback

---

## Environment & Dependencies

### Backend Setup
**Required Environment Variables** (in `backend/.env`):
```
AWS_ACCESS_KEY=<your_key>
AWS_SECRET_KEY=<your_secret>
AWS_REGION=eu-west-1
AWS_BUCKET_NAME=uva-image
FLASK_ENV=development
PORT=5000
```

**Python Runtime:**
- Python 3.11 (per Dockerfile)
- Virtual environment located at `backend/venv/`
- Activation: `source backend/Scripts/activate` (Windows) or `backend/Scripts/Activate.ps1` (PowerShell)

### Frontend Setup
**Node Environment:**
- Next.js 15.5.2 with Turbopack
- Dev server: `npm run dev` (port 3000)
- Build: `npm run build --turbopack`

**Key Dependencies:**
- `axios` for HTTP requests to Flask backend
- `tailwindcss@4` for styling
- `react@19` with TypeScript strict mode

---

## Critical Developer Workflows

### Running Locally

**Backend:**
```bash
cd backend
# Activate venv
source venv/bin/activate  # or Scripts/Activate.ps1 on Windows
# Set Flask env
export FLASK_ENV=development
# Run (port 5000)
python main.py
```

**Frontend:**
```bash
cd frontend/uva
npm install
npm run dev  # port 3000
```

### Testing S3 Integration
- Use `testapi.py` as reference for manual S3 testing (boto3 patterns)
- Health check: `GET http://localhost:5000/health` verifies S3 bucket connection
- Presigned URL generation includes 1-hour expiry by default

### Docker Build & Deploy
**Backend** uses multi-stage build (builder + runtime):
- Stage 1: Installs dependencies in isolated venv
- Stage 2: Minimal runtime image (python:3.11-slim)
- Non-root user execution (appuser)
- Health check via HTTP request to `/health` endpoint
- Note: Dockerfile incomplete (cmd[] missing) - needs completion before production deployment

---

## Code Patterns & Conventions

### S3 Operations Pattern
```python
# Standardized error handling for all S3 operations
try:
    s3.<operation>()
    return _corsify_actual_response(jsonify({...})), 200
except ClientError as e:
    return _corsify_actual_response(handle_s3_error(e))
except Exception as e:
    return _corsify_actual_response(jsonify({'error': '...'})), 500
```

### File Key Generation
S3 keys use predictable structure for organization:
```
uploads/YYYY/MM/DD/filename_HHMMSS.ext
```
Uses `secure_filename()` to prevent path traversal + timestamp to ensure uniqueness.

### Frontend File Validation
- Validate **before** upload attempt (type + size)
- Display human-readable error messages
- Show upload progress state
- Reset status on new file selection

### Flask Configuration Pattern
- Centralized `Config` class with limits and allowed types
- Environment variables loaded via `python-dotenv`
- Logging configured at app startup with timestamps and level filtering

---

## Integration Points & Dependencies

### Frontend ↔ Backend Communication
- **Base URL**: `http://localhost:5000` (development)
- **Content-Type**: Multipart/form-data for file uploads
- **Response Format**: JSON with `message`, `error`, `url`, `key` fields
- **Error Recovery**: Axios error handling displays server error messages to user

### AWS S3 Dependencies
- Bucket must exist and be accessible with provided credentials
- Region must match bucket location (currently `eu-west-1`)
- Presigned URLs valid for 1 hour from generation
- ACL set to `private` - no public access by default

### Deployment Considerations
- S3 bucket name and credentials injected via environment variables
- No hardcoded secrets (loaded from `.env` in dev, secrets manager in prod)
- CORS enabled for frontend domain (currently allows `*`)
- Health check endpoint essential for orchestration (ECS, Kubernetes)

---

## Known Gaps & TODO Items

1. **Backend Dockerfile**: Incomplete - `cmd[]` line missing, needs `CMD ["python", "main.py"]` or Gunicorn configuration
2. **Frontend Dockerfile**: Placeholder only - needs Node.js build stage
3. **Error Handling**: Client-side error messages could include retry logic
4. **Testing**: No unit/integration tests present - recommend pytest for backend, Jest for frontend
5. **AI Analysis**: Future phase - readme mentions CLIP (Hugging Face) integration not yet implemented

---

## Quick Reference: File Locations

| Purpose | Location |
|---------|----------|
| Flask routes & S3 logic | `backend/main.py` |
| Frontend UI & validation | `frontend/uva/src/app/page.tsx` |
| Config & layout | `frontend/uva/src/app/layout.tsx` |
| Build config | `frontend/uva/next.config.ts`, `tsconfig.json` |
| Package deps | `frontend/uva/package.json` |
| Backend Dockerfile | `backend/Dockerfile` |
| Environment secrets | `backend/.env` (git-ignored in production) |

