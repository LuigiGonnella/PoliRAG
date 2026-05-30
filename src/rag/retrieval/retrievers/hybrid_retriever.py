import os
import requests
from qdrant_client import QdrantClient, models
from fastembed import SparseTextEmbedding

class HybridRetriever:
    """
    Performs hybrid search combining dense and sparse (lexical) search through RRF (Reciprocal Rank Fusion)
    """
    def __init__(self, client: QdrantClient, collection_name: str, hf_token: str):
        self.client = client
        self.collection_name = collection_name
        self.hf_token = hf_token
        self.hf_model_url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    def _get_dense_embedding(self, text: str) -> list:
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": [text], "options": {"wait_for_model": True}}
        response = requests.post(self.hf_model_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"HF API Dense Embedding Error: {response.text}")
        return response.json()[0]

    def retrieve(self, query: str, limit: int = 20, query_filter: models.Filter = None):
        dense_vector = self._get_dense_embedding(query)
        
        sparse_embeddings = list(self.sparse_model.embed([query]))
        sparse_vec = sparse_embeddings[0]
        qdrant_sparse_vector = models.SparseVector(
            indices=sparse_vec.indices.tolist(),
            values=sparse_vec.values.tolist()
        )

        # Execute single-trip multi-vector prefetching 
        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(query=dense_vector, using="dense", limit=limit, query_filter=query_filter),
                models.Prefetch(query=qdrant_sparse_vector, using="sparse", limit=limit, query_filter=query_filter)
            ],
            query=models.RrfQuery(rrf=models.Rrf()),
            limit=limit
        )
        return response.points