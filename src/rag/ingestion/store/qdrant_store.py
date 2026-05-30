import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client import models
from utils.utils import extract_path_metadata


RAW_DIR = os.environ.get("DATA_DIR", "D:/PersonalStudy/projects/PoliRAG/data/raw")
VECTOR_SIZE = 384  # Matches BAAI/bge-small-en-v1.5 specifications

def initialize_collection(client: QdrantClient, collection_name: str):
    """Checks and establishes index rules once per runtime session."""
    if not client.collection_exists(collection_name):
        print(f"Creating hybrid collection '{collection_name}' on Qdrant Cloud...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            }
        )
        for field in ["source", "course", "degree_level"]:
            client.create_payload_index(
                collection_name=collection_name, 
                field_name=field, 
                field_schema=models.PayloadSchemaType.KEYWORD
            )

def bulk_store_qdrant(chunks_with_metadata, qdrant_client, collection_name, embedding_model, sparse_model):
    """Processes embeddings using warm pre-loaded hardware instances."""
    try:
        texts = [chunk["text"] for chunk in chunks_with_metadata]
        
        print(f"Computing dense embeddings via PyTorch CUDA for {len(texts)} chunks...")
        local_embeddings = embedding_model.encode(
            texts,
            batch_size=256,  # Maximizes parallel GPU matrix operations
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        print("Computing local sparse BM25 token frequencies...")
        sparse_embeddings = list(sparse_model.embed(texts))

        print("Building point structural records...")
        points = []
        for idx, chunk in enumerate(chunks_with_metadata):
            path_meta = extract_path_metadata(chunk["source"], RAW_DIR)
            unique_string = f"{chunk['source']}_{chunk['index']}"
            deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
            
            s_vec = sparse_embeddings[idx]

            point = models.PointStruct(
                id=deterministic_id,
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

        # Chunk the payload uploads into blocks of 512 points for cloud optimization
        chunk_size = 512
        print(f"Uploading vector records to Qdrant Cloud in chunks of {chunk_size}...")
        for i in range(0, len(points), chunk_size):
            batch = points[i:i + chunk_size]
            qdrant_client.upsert(collection_name=collection_name, wait=True, points=batch)
            print(f"Uploaded points {i} through {min(i + chunk_size, len(points))}...")
            
        print(f"Successfully populated Qdrant Cloud with {len(points)} structured chunks!")

    except Exception as e:
        print(f"Bulk Ingestion pipeline aborted: {str(e)}")