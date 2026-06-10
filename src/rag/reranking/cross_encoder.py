from fastembed.rerank.cross_encoder import TextCrossEncoder


def _coerce_score(value) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, dict):
        for key in ("score", "relevance_score"):
            if key in value:
                return float(value[key])
    for attribute in ("score", "relevance_score"):
        if hasattr(value, attribute):
            return float(getattr(value, attribute))
    return float(value)


class LocalCrossEncoder:
    """Local CPU reranker backed by fastembed."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model = TextCrossEncoder(model_name=model_name)

    def compute_scores(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        return [_coerce_score(score) for score in self.model.rerank(query, documents)]
