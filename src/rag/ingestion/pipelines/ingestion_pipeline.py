"""Optimized end-to-end data ingestion pipeline."""
import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from dotenv import load_dotenv
from src.rag.ingestion.loaders.pdf_loader import chunk_pdf
from src.rag.ingestion.loaders.docx_loader import chunk_docx
from src.rag.ingestion.loaders.generic_loader import chunk_generic_text
from utils.utils import scan
from src.rag.ingestion.store.qdrant_store import initialize_collection, bulk_store_qdrant

load_dotenv()
RAW_DIR = os.environ.get("DATA_DIR", "D:/PersonalStudy/projects/PoliRAG/data/raw")

def main():
    print("Initializing environment and loading local ML embedding models onto CUDA...")
    
    # 1. Initialize models and clients ONCE at the start of the application
    qdrant_url = os.environ.get("QDRANT_URL")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cuda")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    
    collection_name = "uni_docs"
    
    # 2. Establish the collection schema definition before processing any files
    initialize_collection(qdrant_client, collection_name)

    global_chunks_pool = []
    file_count = 0

    print(f"Scanning directories starting from: {RAW_DIR}")
    
    # 3. Collect chunks across files into a single, high-performance processing array
    for file_path in scan(RAW_DIR):
        ext = os.path.splitext(file_path)[1].lower().lstrip('.') # Safely strips the dot (e.g., '.pdf' -> 'pdf')
        chunks = None
        
        try:
            match ext:
                case "pdf":
                    chunks = chunk_pdf(file_path)
                case "docx":
                    chunks = chunk_docx(file_path)
                case _:
                    chunks = chunk_generic_text(file_path)
            
            if chunks:
                global_chunks_pool.extend(chunks)
                file_count += 1
                
        except Exception as file_error:
            print(f"Skipping corrupt or locked file [{file_path}]: {file_error}")

    print(f"\nParsing complete. Extracted a total of {len(global_chunks_pool)} chunks from {file_count} files.")
    
    # 4. Fire the high-density GPU batch matrix transformations and cloud upload
    if global_chunks_pool:
        bulk_store_qdrant(
            chunks_with_metadata=global_chunks_pool,
            qdrant_client=qdrant_client,
            collection_name=collection_name,
            embedding_model=dense_model,
            sparse_model=sparse_model
        )
    else:
        print("Ingestion halted: No valid text chunks discovered.")

if __name__ == "__main__":
    main()