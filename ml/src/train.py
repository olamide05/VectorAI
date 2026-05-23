import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.datasets import mnist
from src.model import build_autoencoder
# from tensorflow.keras.models import Model

# 1. Load data
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# 2. Preprocess
x_train = x_train / 255.0
x_test = x_test / 255.0
# Add noise
noise_factor = 0.3

x_train_noisy = x_train + noise_factor * np.random.normal(
    loc=0.0,
    scale=1.0,
    size=x_train.shape
)

x_test_noisy = x_test + noise_factor * np.random.normal(
    loc=0.0,
    scale=1.0,
    size=x_test.shape
)
x_train_noisy = np.clip(x_train_noisy, 0., 1.)
x_test_noisy = np.clip(x_test_noisy, 0., 1.)

# Flatten (28x28 → 784)
x_train = x_train.reshape(-1, 784)
x_test = x_test.reshape(-1, 784)
x_train_noisy = x_train_noisy.reshape(-1, 784)
x_test_noisy = x_test_noisy.reshape(-1, 784)
# 3. Build model
autoencoder, encoder = build_autoencoder()

# 4. Compile
autoencoder.compile(optimizer='adam', loss='mse')

# 5. Train
autoencoder.fit(
    x_train_noisy, x_train,
    epochs=10,
    batch_size=256,
    validation_data=(x_test_noisy, x_test)
)

# 6. Test reconstruction
decoded_imgs = autoencoder.predict(x_test_noisy[:5])
latent_vectors = encoder.predict(x_test_noisy)
# 7. Visualise
n = 5
plt.figure(figsize=(10, 4))

for i in range(n):

    # Original
    ax = plt.subplot(3, n, i + 1)
    plt.imshow(x_test[i].reshape(28, 28), cmap='gray')
    plt.title("Original")
    plt.axis("off")

    # Noisy
    ax = plt.subplot(3, n, i + 1 + n)
    plt.imshow(x_test_noisy[i].reshape(28, 28), cmap='gray')
    plt.title("Noisy")
    plt.axis("off")

    # Reconstructed
    ax = plt.subplot(3, n, i + 1 + (2 * n))
    plt.imshow(decoded_imgs[i].reshape(28, 28), cmap='gray')
    plt.title("Reconstructed")
    plt.axis("off")
    # Latent space visualisation
    
plt.figure(figsize=(10, 6))

scatter = plt.scatter(
    latent_vectors[:, 0],
    latent_vectors[:, 1],
    c=y_test,
    cmap='tab10',
    s=5
)

plt.colorbar(scatter)
plt.title("Latent Space")
plt.xlabel("Latent Dimension 1")
plt.ylabel("Latent Dimension 2")

plt.show()

plt.show()