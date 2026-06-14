from src.rag.reranking.cross_encoder import LocalCrossEncoder


class RerankerPipeline:
    """Rerank retrieved chunks and attach rerank scores to each returned point."""

    def __init__(self, cache_dir: str | None = None):
        self.reranker = LocalCrossEncoder(cache_dir=cache_dir)

    def run(self, query: str, candidates: list, top_l: int = 10) -> list:
        if not candidates:
            return []

        documents = [hit.payload.get("text", "") if hit.payload else "" for hit in candidates]
        scores = self.reranker.compute_scores(query, documents)
        scored_candidates = list(zip(candidates, scores))
        scored_candidates.sort(key=lambda item: item[1], reverse=True)

        reranked = []
        for candidate, score in scored_candidates[:top_l]:
            if candidate.payload is None:
                candidate.payload = {}
            candidate.payload["rerank_score"] = float(score)
            reranked.append(candidate)
        return reranked
