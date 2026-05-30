import os
import uuid
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client import models
from sentence_transformers import SentenceTransformer
from utils.utils import extract_path_metadata
from fastembed import SparseTextEmbedding

# 1. Cloud Database Credentials (Get these from your Qdrant Cloud Console)
QDRANT_URL = os.environ.get("QDRANT_URL", "https://your-qdrant-cluster-url.aws.cloud.qdrant.io:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "your-secure-qdrant-cloud-api-key")

# 2. Local Absolute Path to your university files
RAW_DIR = Path(r"D:/PersonalStudy/projects/PoliRAG/data/raw")
VECTOR_SIZE = 384  # Dimension size for all-MiniLM-L6-v2

def bulk_store_qdrant(chunks_with_metadata):
    if not chunks_with_metadata:
        print("No chunks to process.")
        return

    try:
        # Load the model directly into your local computer's memory (CPU or GPU)
        print("Loading local embedding models...")
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        
        # Connect to your remote cloud database
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        collection_name = "uni_docs"

        # Initialize remote collection schemas
        if not qdrant_client.collection_exists(collection_name):
            print(f"Creating hybrid collection '{collection_name}' on Qdrant Cloud...")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
                }
            )
            for field in ["source", "course", "degree_level"]:
                qdrant_client.create_payload_index(
                    collection_name=collection_name, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD
                )

        print(f"Computing local embeddings for {len(chunks_with_metadata)} text blocks...")
        texts = [chunk["text"] for chunk in chunks_with_metadata]
        
        # Free processing using your local hardware
        local_embeddings = embedding_model.encode(texts, batch_size=32, show_progress_bar=True)
        
        # Compute the sparse vectors for the entire batch of text elements at once
        sparse_embeddings = list(sparse_model.embed(texts))

        points = []
        for idx, chunk in enumerate(chunks_with_metadata):
            path_meta = extract_path_metadata(chunk["source"], RAW_DIR)
            unique_string = f"{chunk['source']}_{chunk['index']}"
            deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
            
            # Pull down the individual sparse map corresponding to this specific item index
            s_vec = sparse_embeddings[idx]

            point = models.PointStruct(
                id=deterministic_id,
                # Convert numpy arrays to standard Python lists for native Qdrant storage wire matching
                vector={
                    "dense": local_embeddings[idx].tolist(),
                    "sparse": models.SparseVector(indices=s_vec.indices.tolist(), values=s_vec.values.tolist())
                },
                payload={
                    "index": chunk["index"],
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "course": path_meta["course"],
                    "degree_level": path_meta["degree_level"],
                    "year": path_meta["year"]
                }
            )
            points.append(point)

        print("Uploading vector points to Qdrant Cloud...")
        qdrant_client.upsert(collection_name=collection_name, wait=True, points=points)
        print(f"Successfully populated Qdrant Cloud with {len(points)} structured chunks!")

    except Exception as e:
        print(f"Bulk Ingestion pipeline aborted: {str(e)}")