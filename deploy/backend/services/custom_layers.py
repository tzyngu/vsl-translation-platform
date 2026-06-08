def positional_embedding_class():
    import tensorflow as tf

    @tf.keras.utils.register_keras_serializable(package="VSL")
    class PositionalEmbedding(tf.keras.layers.Layer):
        def __init__(self, sequence_length, feature_dim, **kwargs):
            super().__init__(**kwargs)
            self.sequence_length = sequence_length
            self.feature_dim = feature_dim
            self.embedding = tf.keras.layers.Embedding(sequence_length, feature_dim)

        def call(self, inputs):
            positions = tf.range(start=0, limit=self.sequence_length, delta=1)
            return inputs + self.embedding(positions)

        def build(self, input_shape):
            self.embedding.build((self.sequence_length,))
            super().build(input_shape)

        def get_config(self):
            config = super().get_config()
            config.update({"sequence_length": self.sequence_length, "feature_dim": self.feature_dim})
            return config

    return PositionalEmbedding
