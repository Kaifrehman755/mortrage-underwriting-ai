"""Dense vector embedding service.

Adheres to Playbook Section 2 & 4:
- Target dimension: 384 dimensions (matching BAAI/bge-small-en-v1.5).
- Emits unit-normalized vectors where dot_product == cosine_similarity.
- Uses sentence-transformers when installed, with a fast deterministic
  random projection fallback ensuring offline reproducibility.
"""

import hashlib
import math
import re
from typing import Any

import numpy as np


class EmbeddingService:
    """Computes 384-dimensional dense semantic embeddings for regulatory text and queries."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._st_model: Any = None
        self._projection_matrix: np.ndarray | None = None

        # Attempt to load sentence-transformers if available
        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer(model_name)
        except Exception:
            self._st_model = None

    def _get_projection_matrix(self) -> np.ndarray:
        """Create a fixed, reproducible random projection matrix for 384 dimensions."""
        if self._projection_matrix is None:
            # Deterministic projection matrix seeded by model name
            rng = np.random.default_rng(20261010)
            vocab_buckets = 4096
            # Sparse projection
            self._projection_matrix = rng.normal(0.0, 1.0 / math.sqrt(self.dimension), (vocab_buckets, self.dimension))
        return self._projection_matrix

    def embed_text(self, text: str) -> list[float]:
        """Generate a 384-dim normalized embedding for a single string."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        if self._st_model is not None:
            raw_embeddings = self._st_model.encode(texts, normalize_embeddings=True)
            return [vec.tolist() for vec in raw_embeddings]

        # Deterministic feature hashing projection
        matrix = self._get_projection_matrix()
        num_buckets = matrix.shape[0]

        results: list[list[float]] = []
        for text in texts:
            tokens = self._tokenize(text)
            if not tokens:
                # Return uniform unit vector
                vec = np.ones(self.dimension) / math.sqrt(self.dimension)
                results.append(vec.tolist())
                continue

            # Bag of words / n-grams into hash buckets
            bow = np.zeros(num_buckets)
            for token in tokens:
                h = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16) % num_buckets
                bow[h] += 1.0

            # Project into 384-dimensional dense space
            dense = bow @ matrix

            # Normalize to unit vector (L2 norm)
            norm = np.linalg.norm(dense)
            if norm > 0:
                dense = dense / norm
            else:
                dense = np.ones(self.dimension) / math.sqrt(self.dimension)

            results.append([round(float(x), 6) for x in dense])

        return results

    def _tokenize(self, text: str) -> list[str]:
        """Extract alphanumeric unigrams and bigrams for lexical-semantic projection."""
        words = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
        return words + bigrams
