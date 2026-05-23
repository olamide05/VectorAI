from tensorflow.keras import layers, models

def build_autoencoder(input_dim=784, latent_dim=2):
    
    #  Encoder
    input_layer = layers.Input(shape=(input_dim,))
    x = layers.Dense(128, activation='relu')(input_layer)
    x = layers.Dense(32, activation='relu')(x)
    latent = layers.Dense(latent_dim)(x)
    
    #  Decoder
    x = layers.Dense(32, activation='relu')(latent)
    x = layers.Dense(128, activation='relu')(x)
    output_layer = layers.Dense(input_dim, activation='sigmoid')(x)
    
    # Full model
    autoencoder = models.Model(input_layer, output_layer)
    encoder = models.Model(input_layer, latent)
    return autoencoder, encoder