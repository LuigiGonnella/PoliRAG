import os
import requests
from qdrant_client import QdrantClient, models

class VectorRetriever:
    """
    Performes dense retrieval through cosine-similarity
    """
    def __init__(self, client: QdrantClient, collection_name: str, hf_token: str):
        self.client = client
        self.collection_name = collection_name
        self.hf_token = hf_token
        self.hf_model_url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

    def _get_embedding(self, text: str) -> list:
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": [text], "options": {"wait_for_model": True}}
        response = requests.post(self.hf_model_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"HF API Dense Embedding Error: {response.text}")
        return response.json()[0]

    def retrieve(self, query: str, limit: int = 20, query_filter: models.Filter = None):
        vector = self._get_embedding(query)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            using="dense",
            query_filter=query_filter,
            limit=limit
        )
        return response.points