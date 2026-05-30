from reranking.cross_encoder import LocalCrossEncoder

class RerankerPipeline:
    """
    Given the TOP-K retrieved chunks after hybrid search, performs re-ranking and gets TOP-L final chunks
    """
    def __init__(self):
        self.reranker = LocalCrossEncoder()

    def run(self, query: str, candidates: list, top_l: int = 5) -> list:
        if not candidates:
            return []

        # 1. Unpack textual payloads
        documents = [hit.payload.get("text", "") for hit in candidates]

        # 2. Extract Cross-Encoder relevance scores
        scores = self.reranker.compute_scores(query, documents)

        # 3. Zip data, sort elements in descending order
        scored_candidates = list(zip(candidates, scores))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # 4. Extract Top-L points
        return [item[0] for item in scored_candidates[:top_l]]