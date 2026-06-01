"""Collection storage architecture mapping and streaming routines."""
import os
import uuid
import json
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client import models
from utils.utils import extract_path_metadata

RAW_DIR = os.environ.get("DATA_DIR", "C:/Users/Utente/OneDrive - Politecnico di Torino/Universita")
VECTOR_SIZE = 384  # Matches BAAI/bge-small-en-v1.5 specifications

def initialize_collection(qdrant_client, collection_name):
    """Establishes named schemas and quantization models in the vector space."""
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                    quantization_config=models.ScalarQuantization(
                        scalar=models.ScalarQuantizationConfig(
                            type=models.ScalarType.INT8,
                            always_ram=True
                        )
                    )
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams()
            }
        )

def bulk_store_qdrant(chunks_with_metadata, qdrant_client, collection_name, embedding_model, sparse_model):
    """Processes embeddings and streams payload batches securely to Qdrant Cloud."""
    try:
        texts = [chunk["text"] for chunk in chunks_with_metadata]
        
        print(f"Computing dense embeddings via PyTorch CUDA for {len(texts)} chunks...")
        local_embeddings = embedding_model.encode(
            texts,
            batch_size=256,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        print("Computing local sparse BM25 token frequencies...")
        sparse_embeddings = list(sparse_model.embed(texts))

        print("Building point structural records...")
        points = []
        base_dir_obj = Path(RAW_DIR)

        for idx, chunk in enumerate(chunks_with_metadata):
            path_meta = extract_path_metadata(chunk["source"], RAW_DIR)
            
            # ===============================================================
            # PATH SANITIZATION: Strip OneDrive path and isolate relative tree
            # ===============================================================
            try:
                # Isolate the tail path starting after your raw tracking boundary
                relative_path = Path(chunk["source"]).relative_to(base_dir_obj)
                # Combine the target base folder name ("Universita") with the relative path
                cleaned_source_str = str(Path(base_dir_obj.name) / relative_path).replace("/", "\\")
            except Exception:
                # Safe fallback to prevent string parsing errors from crashing extraction runs
                cleaned_source_str = chunk["source"]

            normalized_source = str(Path(chunk["source"]).as_posix())
            unique_string = f"{normalized_source}_{chunk['index']}"
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
                    "source": cleaned_source_str,  # Stores clean, standardized paths
                    "course": path_meta["course"],
                    "degree_level": path_meta["degree_level"],
                    "year": path_meta["year"]
                }
            )
            points.append(point)

        chunk_size = 512
        print(f"Uploading vector records to Qdrant Cloud in chunks of {chunk_size}...")
        for i in range(0, len(points), chunk_size):
            batch = points[i:i + chunk_size]
            qdrant_client.upsert(collection_name=collection_name, wait=True, points=batch)
            print(f"Uploaded points {i} through {min(i + chunk_size, len(points))}...")
            
        print(f"Successfully populated Qdrant Cloud with {len(points)} structured chunks!")
        return True  # Signal successful transactional complete state

    except Exception as e:
        print(f"Bulk Ingestion pipeline aborted: {str(e)}")
        return False  # Block the logging file tracking path on failures