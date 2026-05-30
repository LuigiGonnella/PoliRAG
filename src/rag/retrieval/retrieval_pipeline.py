from qdrant_client import QdrantClient, models
from retrieval.retrievers.hybrid_retriever import HybridRetriever

class RetrievalPipeline:
    def __init__(self, client: QdrantClient, collection_name: str, hf_token: str):
        self.retriever = HybridRetriever(client, collection_name, hf_token)

    def run(self, query: str, top_k: int = 20, course_filter: str = None, degree_filter: str = None):
        filter_conditions = []
        if course_filter:
            filter_conditions.append(models.FieldCondition(key="course", match=models.MatchValue(value=course_filter)))
        if degree_filter:
            filter_conditions.append(models.FieldCondition(key="degree_level", match=models.MatchValue(value=degree_filter)))
            
        query_filter = models.Filter(must=filter_conditions) if filter_conditions else None

        # Return Stage 1 candidates (Top-K)
        return self.retriever.retrieve(query, limit=top_k, query_filter=query_filter)