from fastembed.rerank.cross_encoder import TextCrossEncoder

class LocalCrossEncoder:
    """
    Performs re-ranking basing on coupled cevaluation between the query and each retrieved chunk
    """
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        # Quantized CPU architecture framework
        self.model = TextCrossEncoder(model_name=model_name)

    def compute_scores(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        # Returns raw float relevance probabilities matching index position arrays
        return list(self.model.rerank(query, documents))