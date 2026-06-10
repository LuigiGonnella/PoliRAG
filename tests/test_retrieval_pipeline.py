from src.rag.retrieval.retrieval_pipeline import RetrievalPipeline


class FakeRetriever:
    def __init__(self):
        self.query_filter = None
        self.limit = None

    def retrieve(self, query, limit, query_filter):
        self.limit = limit
        self.query_filter = query_filter
        return []


def test_retrieval_pipeline_builds_course_year_degree_filter():
    fake = FakeRetriever()
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    pipeline.retriever = fake

    result = pipeline.run(
        "backpropagation",
        top_k=7,
        course_filter="MachineLearning_for_Vision_and_Multimedia",
        degree_filter="Magistrale",
        year_filter="Primo Anno",
    )

    assert result == []
    assert fake.limit == 7
    keys = {condition.key for condition in fake.query_filter.must}
    assert keys == {"course", "degree_level", "year"}
