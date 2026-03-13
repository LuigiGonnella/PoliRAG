"""End-to-end data ingestion pipeline."""
# Configurable parent directory (can be overridden by env var POLIRAG_PARENT_DIR)
PARENT_DIR = Path(os.environ.get("POLIRAG_PARENT_DIR", r"D:/PersonalStudy/projects/PoliRAG"))

# Derived paths
RAW_DATA_PATH = PARENT_DIR / "data" / "raw"
VECTOR_DB_PATH = PARENT_DIR / "data" / "vector_db"
from pathlib import Path
import os
from ingestion.loaders.pdf_loader import chunk_pdf
from ingestion.loaders.docx_loader import chunk_docx
from ingestion.loaders.generic_loader import chunk_generic_text
from utils.utils import scan
from ingestion.store.qdrant_store import store_qdrant

def main():

    main_folder = RAW_DATA_PATH

    #Iterate over subfolders
    for file_path in scan(main_folder):
        file_split = os.path.splitext(file_path)
        extension = file_split[1] #.txt, .C, .PY, ...
        chunks = None
        match extension:
            case "pdf":
                chunks = chunk_pdf(file_path)
              
            case "docx":
                chunks  = chunk_docx(file_path)
              
            case _:
                chunks  = chunk_generic_text(file_path)

        if chunks is not None:
            store_qdrant(chunks)

        

if __name__ == "__main__":
    main()