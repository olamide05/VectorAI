# VectorAI

A full-stack platform combining cloud-based image processing with machine learning experimentation — built to explore autoencoder compression, latent space representations, and real image-pipeline infrastructure end to end.

## Results

- TensorFlow autoencoders compress 784-dimensional image inputs into latent spaces as small as **2 dimensions** — a **~392x compression ratio** — for reconstruction and denoising experiments.
- Real AWS Rekognition integration performs automated image labelling and OCR text extraction on uploaded images (not a stub — this is live in the Flask backend).

## Features

- Flask APIs for file upload, OCR extraction, image labelling, and metadata management
- AWS S3 storage integration for uploaded assets
- AWS Rekognition integration for automated labelling and OCR
- TensorFlow autoencoder architectures for compression, reconstruction, and denoising experiments
- React/TypeScript frontend

## Architecture

```
backend/   — Flask API: uploads, S3 storage, Rekognition (OCR + labelling), metadata
ml/        — TensorFlow autoencoder: model definition, training
frontend/  — React/TypeScript client
```

## Tech Stack

Python, Flask, TensorFlow, AWS (S3, Rekognition), React, TypeScript

## Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set required environment variables (see backend/config.py)
# AWS credentials, S3 bucket name, etc. — do not commit these

# Run
python main.py
```

## Notes

This is an ongoing personal project — some pieces (ML serving infrastructure, similarity search over embeddings) are actively being extended. The core pipeline (upload → S3 storage → labelling/OCR → autoencoder compression) is functional end to end.
