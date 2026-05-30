from qdrant_client import QdrantClient, models
from fastembed import SparseTextEmbedding

class BM25Retriever:
    """
    Performs lexical search through BM25 formula
    """
    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name
        # Generates small, fast token maps using local ONNX
        self.model = SparseTextEmbedding(model_name="Qdrant/bm25")

    def retrieve(self, query: str, limit: int = 20, query_filter: models.Filter = None):
        sparse_embeddings = list(self.model.embed([query]))
        sparse_vec = sparse_embeddings[0]
        
        qdrant_sparse_vector = models.SparseVector(
            indices=sparse_vec.indices.tolist(),
            values=sparse_vec.values.tolist()
        )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=qdrant_sparse_vector,
            using="sparse",
            query_filter=query_filter,
            limit=limit
        )
        return response.points