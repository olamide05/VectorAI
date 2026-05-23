# VectorAI

## Overview

VectorAI is an experimental machine learning system focused on neural data compression using autoencoders.

The project explores how neural networks can learn compact latent representations of images while preserving important visual information for reconstruction.

Rather than storing raw pixel data directly, VectorAI compresses images into low-dimensional vectors inside a learned latent space.

This project combines:
- Deep Learning
- Representation Learning
- Data Compression
- Visualization
- Full-stack integration

---

# Core Idea

Traditional image compression uses handcrafted algorithms.

VectorAI instead learns compression automatically using neural networks.

The encoder transforms high-dimensional image data into compact latent vectors:

```text
784 dimensions → 128 → 32 → 2 dimensions
```

The decoder reconstructs the image from this compressed representation.

This demonstrates how machine learning models learn meaningful internal representations of data.

---

# Architecture

```text
Input Image (28x28)
        ↓
Flatten (784)
        ↓
Encoder Network
784 → 128 → 32 → 2
        ↓
Latent Space
        ↓
Decoder Network
2 → 32 → 128 → 784
        ↓
Reconstructed Image
```

---

# Features

- Autoencoder-based image compression
- Latent space visualization
- Image reconstruction
- Denoising autoencoder experiments
- Compression quality analysis
- Reconstruction loss tracking
- MNIST dataset integration

---

# Current Experiments

## Basic Autoencoder

The model learns compressed representations of handwritten digits.

### Reconstruction Example

- Original image
- Compressed latent representation
- Reconstructed output

---

## Latent Space Visualization

The encoder maps visually similar digits close together inside latent space.

This allows:
- clustering analysis
- representation learning
- dimensionality reduction

---

## Denoising Autoencoder

Noise is added to images before compression.

The model learns to:
- remove noise
- preserve structure
- reconstruct cleaner outputs

This demonstrates robustness in learned representations.

---

# Concepts Explored

- Autoencoders
- Latent Space
- Representation Learning
- Neural Compression
- Reconstruction Loss
- Denoising
- Dimensionality Reduction
- Feature Extraction

---

# Tech Stack

## Machine Learning
- TensorFlow / Keras
- NumPy
- Matplotlib

## Frontend
- React
- TypeScript
- Next.js

## Backend
- Python

---

# Project Structure

```text
VectorAI/
│
├── backend/
├── frontend/
├── ml/
│   ├── src/
│   │   ├── model.py
│   │   ├── train.py
│   │   └── utils.py
│   │
│   ├── saved_models/
│   └── notebooks/
│
├── docs/
├── README.md
└── .gitignore
```

---

# Running the ML Pipeline

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run training

```bash
python train.py
```

---

# Results

## Reconstruction Quality

The model successfully reconstructs compressed MNIST digits using only a 2-dimensional latent representation.

### Observations

- Larger latent dimensions improve reconstruction quality
- Smaller latent dimensions improve compression ratio
- Similar digits cluster together in latent space

---

# Goals

- Understand learned data representations
- Explore neural compression systems
- Build production-style ML pipelines
- Integrate ML systems into full-stack applications
- Experiment with advanced generative architectures

---

# Future Improvements

- Variational Autoencoders (VAE)
- Convolutional Autoencoders
- Real image datasets
- Model checkpointing
- Web deployment
- Interactive latent space explorer
- Cloud inference APIs
- GPU optimization

---

# Author

Mahmoud Olamide Alimi

Software Engineering & AI Engineering
