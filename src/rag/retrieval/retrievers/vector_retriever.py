import os

from qdrant_client import QdrantClient, models

from src.rag.models.fastembed_cache import get_text_embedding


class VectorRetriever:
    """Dense cosine-similarity retriever."""

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        hf_token: str | None,
        hf_embedding_model: str = "BAAI/bge-small-en-v1.5",
        cache_dir: str | None = None,
    ):
        self.client = client
        self.collection_name = collection_name
        self.hf_token = hf_token
        if hf_token:
            os.environ.setdefault("HF_TOKEN", hf_token)
        self.dense_model = get_text_embedding(hf_embedding_model, cache_dir)

    def _get_embedding(self, text: str) -> list:
        embedding = next(iter(self.dense_model.embed([text])))
        return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)

    def retrieve(self, query: str, limit: int = 20, query_filter: models.Filter | None = None):
        vector = self._get_embedding(query)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            using="dense",
            query_filter=query_filter,
            limit=limit,
        )
        return response.points
