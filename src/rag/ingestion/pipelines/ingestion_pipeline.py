"""Optimized end-to-end data ingestion pipeline."""
import os
from dotenv import load_dotenv

# 1. Initialize environment configurations before loading project dependencies
load_dotenv()

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from src.rag.ingestion.loaders.pdf_loader import chunk_pdf
from src.rag.ingestion.loaders.docx_loader import chunk_docx
from src.rag.ingestion.loaders.generic_loader import chunk_generic_text
from utils.utils import scan
from src.rag.ingestion.store.qdrant_store import initialize_collection, bulk_store_qdrant
import torch
from pathlib import Path
import json
# ===========================================================================
# PYTORCH 2.6+ UNPICKLER BUGFIX
# Enforces weights_only=False globally to allow structural legacy checkpoints
# ===========================================================================
_original_torch_load = torch.load

def _trusted_torch_load(*args, **kwargs):
    """Enforces weights_only=False to support legacy structural checkpoints."""
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

# Overwrite the global torch loading handler at the process root level
torch.load = _trusted_torch_load
# ===========================================================================

RAW_DIR = os.environ.get("DATA_DIR", "C:/Users/Utente/OneDrive - Politecnico di Torino/Universita")
# Define storage directories
CACHE_DIR = Path("D:/PersonalStudy/projects/PoliRAG/data/processed_chunks")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TRACKING_FILE = CACHE_DIR / "processed_files.log"

def load_processed_files():
    if TRACKING_FILE.exists():
        return set(TRACKING_FILE.read_text().splitlines())
    return set()

def log_processed_file(file_path):
    with open(TRACKING_FILE, "a") as f:
        f.write(f"{file_path}\n")

def main():
    print("Initializing environment and loading local ML embedding models onto CUDA...")
    
    qdrant_url = os.environ.get("QDRANT_URL")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cuda")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    
    collection_name = "uni_docs"
    initialize_collection(qdrant_client, collection_name)

    processed_files = load_processed_files()
    print(f"Scanning directories starting from: {RAW_DIR}")
    
    for file_path in scan(RAW_DIR):
        if file_path in processed_files:
            print(f"Skipping already ingested file: {os.path.basename(file_path)}")
            continue

        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        chunks = None
        
        # Generate clean identifier for local JSON caching
        safe_cache_name = f"{Path(file_path).stem}_{ext}.json"
        cache_file_path = CACHE_DIR / safe_cache_name

        try:
            # Check if this file was already parsed by Magic-PDF previously
            if cache_file_path.exists():
                print(f"Loading cached chunks for {os.path.basename(file_path)}...")
                with open(cache_file_path, "r", encoding="utf-8") as cf:
                    chunks = json.load(cf)
            else:
                # Run the heavy extraction engines
                match ext:
                    case "pdf": chunks = chunk_pdf(file_path)
                    case "docx": chunks = chunk_docx(file_path)
                    case _: chunks = chunk_generic_text(file_path)
                
                # Instantly drop chunks to disk to protect CPU/GPU processing investments
                if chunks:
                    with open(cache_file_path, "w", encoding="utf-8") as cf:
                        json.dump(chunks, cf, ensure_ascii=False, indent=2)

            # Stream chunks to Qdrant immediately for this file
            if chunks:
                print(f"Streaming {len(chunks)} chunks from {os.path.basename(file_path)} to Qdrant Cloud...")
                was_stored_successfully = bulk_store_qdrant(
                    chunks_with_metadata=chunks,
                    qdrant_client=qdrant_client,
                    collection_name=collection_name,
                    embedding_model=dense_model,
                    sparse_model=sparse_model
                )
                
                # TRANSACTIONAL GUARD: Only log to success file if no internal failures occurred
                if was_stored_successfully:
                    log_processed_file(file_path)
                else:
                    print(f"ERROR: Ingestion tracking skipped for [{os.path.basename(file_path)}] due to upload errors.")
                
        except Exception as file_error:
            print(f"Skipping corrupt or locked file [{file_path}]: {file_error}")

    print("\nIngestion run completed successfully.")

if __name__ == "__main__":
    main()