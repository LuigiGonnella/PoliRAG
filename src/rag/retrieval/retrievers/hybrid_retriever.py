import os

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models


class HybridRetriever:
    """Hybrid dense/sparse retriever using Qdrant RRF fusion."""

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        hf_token: str | None,
        hf_embedding_model: str = "BAAI/bge-small-en-v1.5",
    ):
        self.client = client
        self.collection_name = collection_name
        self.hf_token = hf_token
        if hf_token:
            os.environ.setdefault("HF_TOKEN", hf_token)
        self.dense_model = TextEmbedding(model_name=hf_embedding_model)
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    def _get_dense_embedding(self, text: str) -> list:
        embedding = next(iter(self.dense_model.embed([text])))
        return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)

    def retrieve(self, query: str, limit: int = 20, query_filter: models.Filter | None = None):
        dense_vector = self._get_dense_embedding(query)

        sparse_embeddings = list(self.sparse_model.embed([query]))
        sparse_vec = sparse_embeddings[0]
        qdrant_sparse_vector = models.SparseVector(
            indices=sparse_vec.indices.tolist(),
            values=sparse_vec.values.tolist(),
        )

        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(query=dense_vector, using="dense", limit=limit, filter=query_filter),
                models.Prefetch(query=qdrant_sparse_vector, using="sparse", limit=limit, filter=query_filter),
            ],
            query=models.RrfQuery(rrf=models.Rrf()),
            limit=limit,
        )
        return response.points
