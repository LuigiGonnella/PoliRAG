"""PDF content parser using local MinerU (magic-pdf) core execution engine."""
import os
from src.rag.ingestion.cleaners.text_cleaner import clean_text
from chunking.chunk_manager import line_text_splitter

# Native MinerU local pipeline modules
from magic_pdf.pipe.UNIPipe import UNIPipe

try:
    # Handles folder writer definitions across diverse MinerU local installs
    from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter
except ImportError:
    from magic_pdf.data.data_reader_writer import DiskReaderWriter

# 1000 characters evaluates to ~250-330 tokens, safely below BGE-small's 512 context limit
CHUNK_SIZE = 1000 

def chunk_pdf(path):
    """
    Parses a PDF file locally using magic-pdf, chunking content to fit embedding 
    token limits while preserving precise 1-based page metadata index arrays.
    """
    chunks_with_metadata = []
    filename = os.path.basename(path)
    basename = os.path.splitext(filename)[0]

    print(f"Starting local MinerU CUDA extraction for: {filename}")
    
    try:
        # 1. Read raw PDF file data as bytes
        with open(path, "rb") as f:
            pdf_bytes = f.read()

        # 2. Setup a local directory for any extracted structural media assets/images
        local_image_dir = os.path.join(os.path.dirname(path), f"{basename}_extracted_media")
        os.makedirs(local_image_dir, exist_ok=True)
        image_writer = DiskReaderWriter(local_image_dir)

        # 3. Feed elements to the native multi-stage model processing wrapper
        jso_useful_key = {"_pdf_type": "", "model_list": []}
        pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
        
        pipe.pipe_classify()  # Layout classification pass
        pipe.pipe_analyze()   # Layout element mapping structure analysis
        pipe.pipe_parse()     # Core vision-language text, table, and math extraction loops

        # 4. Extract the universal standardized model structure list items
        content_list = pipe.pipe_mk_uni_format()

        # 5. Cluster parsed text blocks page-by-page 
        page_content_map = {}
        for block in content_list:
            page_num = block.get("page_idx", 0) + 1  # 1-based page numbering for exact RAG references
            block_type = block.get("type")
            
            if block_type in ["text", "table", "equation", "formula", "title"]:
                content = block.get("text", "") or block.get("content", "")
                if content.strip():
                    page_content_map.setdefault(page_num, []).append(content)

        # 6. Step through aggregated pages and check character dimensions
        for page_num in sorted(page_content_map.keys()):
            page_text = "\n".join(page_content_map[page_num]) + "\n"
            cleaned_page_text = clean_text(page_text)
            
            if cleaned_page_text.strip():
                # Keep safe-length pages whole to maximize text cohesion
                if len(cleaned_page_text) <= 1200:
                    chunks_with_metadata.append({
                        "text": cleaned_page_text,
                        "index": page_num,
                        "source": path
                    })
                else:
                    # Slice text safely below embedding model context limits
                    sub_chunks = line_text_splitter(cleaned_page_text, CHUNK_SIZE)
                    for sub_chunk in sub_chunks:
                        if sub_chunk.strip():
                            chunks_with_metadata.append({
                                "text": sub_chunk,
                                "index": page_num,  # Tracks sub-chunks to the identical origin page
                                "source": path
                            })

    except Exception as e:
        print(f"Local MinerU parsing error failed on document {filename}: {str(e)}")

    print(f"DOCUMENT {basename} chunking completed successfully! Generated {len(chunks_with_metadata)} chunks.")
    return chunks_with_metadata