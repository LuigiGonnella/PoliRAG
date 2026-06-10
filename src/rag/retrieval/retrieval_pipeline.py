from qdrant_client import QdrantClient, models

from src.rag.retrieval.retrievers.hybrid_retriever import HybridRetriever


class RetrievalPipeline:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        hf_token: str | None,
        hf_embedding_model: str = "BAAI/bge-small-en-v1.5",
    ):
        self.retriever = HybridRetriever(client, collection_name, hf_token, hf_embedding_model)

    def run(
        self,
        query: str,
        top_k: int = 25,
        course_filter: str | None = None,
        degree_filter: str | None = None,
        year_filter: str | None = None,
    ):
        filter_conditions = []
        if course_filter:
            filter_conditions.append(
                models.FieldCondition(key="course", match=models.MatchValue(value=course_filter))
            )
        if degree_filter:
            filter_conditions.append(
                models.FieldCondition(key="degree_level", match=models.MatchValue(value=degree_filter))
            )
        if year_filter:
            filter_conditions.append(
                models.FieldCondition(key="year", match=models.MatchValue(value=year_filter))
            )

        query_filter = models.Filter(must=filter_conditions) if filter_conditions else None
        return self.retriever.retrieve(query, limit=top_k, query_filter=query_filter)
