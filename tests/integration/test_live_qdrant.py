import os

import pytest
from dotenv import load_dotenv
from qdrant_client import QdrantClient

from src.rag.retrieval.retrieval_pipeline import RetrievalPipeline


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_QDRANT_TESTS") != "1",
    reason="Set RUN_QDRANT_TESTS=1 to run live Qdrant tests.",
)


@pytest.fixture(scope="module")
def qdrant_client():
    load_dotenv()
    return QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ.get("QDRANT_API_KEY") or None,
    )


def test_live_qdrant_collection_exists(qdrant_client):
    collection = os.environ.get("QDRANT_COLLECTION", "uni_docs")
    assert qdrant_client.collection_exists(collection)


def test_live_qdrant_has_course_metadata(qdrant_client):
    collection = os.environ.get("QDRANT_COLLECTION", "uni_docs")
    points, _ = qdrant_client.scroll(
        collection_name=collection,
        limit=10,
        with_payload=["course", "degree_level", "year"],
        with_vectors=False,
    )
    assert points
    assert any((point.payload or {}).get("course") for point in points)


def test_live_hybrid_retrieval_returns_context(qdrant_client):
    if not os.environ.get("HF_API_TOKEN"):
        pytest.skip("HF_API_TOKEN is required for live retrieval.")

    collection = os.environ.get("QDRANT_COLLECTION", "uni_docs")
    pipeline = RetrievalPipeline(
        qdrant_client,
        collection,
        os.environ.get("HF_API_TOKEN"),
        hf_embedding_model=os.environ.get("HF_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
    )
    results = pipeline.run("machine learning gradient descent", top_k=3)
    assert results
    assert any((point.payload or {}).get("text") for point in results)
