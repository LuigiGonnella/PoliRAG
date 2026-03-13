from pathlib import Path
import os
PARENT_DIR = Path(os.environ.get("POLIRAG_PARENT_DIR", r"D:/PersonalStudy/projects/PoliRAG"))
QDRANT_STORE_PATH = PARENT_DIR / "data" / "vector_db" / "qdrant_store"
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid

def store_qdrant(chunks_with_metadata):

    try:

        client = QdrantClient(QDRANT_STORE_PATH)
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        collection_name = "uni_docs"
        vector_size = 384

        client.create_collection(
            collection_name = collection_name,
            vectors_config = VectorParams(size=vector_size, distance=Distance.COSINE)
        )

        points = []
        for chunk in chunks_with_metadata:
            embedding = embedding_model.encode(chunk["text"])

            point = PointStruct(
                id = uuid.uuid4(),
                vector = embedding,
                payload = {
                    "index" : chunk["index"],
                    "text": chunk["text"],
                    'source': chunk["source"]
                }
            )
            points.append(point)

        #Insert collection
        operation_info = client.upsert(
            collection_name = collection_name,
            wait = True,
            points = points
        )

    except Exception as e:
        print(f"Error occurred: {str(e)}")

    
    print(f"Insertion status: {operation_info.status}")
    print(f"Successfully inserted {len(points)} chunks into Qdrant")