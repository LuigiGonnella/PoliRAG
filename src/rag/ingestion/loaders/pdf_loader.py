"""PDF content parser using the modern Magic-PDF (v1.3+) Dataset API."""
import os
from src.rag.ingestion.cleaners.text_cleaner import clean_text
from chunking.chunk_manager import line_text_splitter

# Import official modern V1.3+ Magic-PDF dataset components
from magic_pdf.data.data_reader_writer import FileBasedDataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

# 1000 characters evaluates to ~250-330 tokens, safely below BGE-small's 512 context limit
CHUNK_SIZE = 1000 

def chunk_pdf(path):
    """
    Parses a PDF file using the modern Magic-PDF v1.3 API, chunking content 
    safely to fit embedding token limits while preserving 1-based page metadata.
    """
    chunks_with_metadata = []
    filename = os.path.basename(path)
    basename = os.path.splitext(filename)[0]

    print(f"Starting local Magic-PDF v1.3 extraction for: {filename}")
    
    try:
        # 1. Read raw PDF file content as bytes
        with open(path, "rb") as f:
            pdf_bytes = f.read()

        # 2. Setup a local directory for any extracted visual assets
        local_image_dir = os.path.join(os.path.dirname(path), f"{basename}_extracted_media")
        os.makedirs(local_image_dir, exist_ok=True)
        image_writer = FileBasedDataWriter(local_image_dir)
        image_dir_name = str(os.path.basename(local_image_dir))

        # 3. Create modern Dataset Instance
        ds = PymuDocDataset(pdf_bytes)

        # 4. Classify and execute the matching parsing pipeline (TXT or OCR mode)
        if ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)

        # 5. Extract structural layout blocks using the modern API method
        content_list = pipe_result.get_content_list(image_dir_name)

        # 6. Group extracted content blocks page-by-page
        page_content_map = {}
        for block in content_list:
            # page_idx is 0-indexed, turn into 1-indexed for student-facing citations
            page_num = block.get("page_idx", 0) + 1  
            block_type = block.get("type")
            
            # Extract text elements, titles, tables, and raw formulas
            if block_type in ["text", "table", "equation", "formula", "title"]:
                content = block.get("text", "") or block.get("content", "")
                if content and content.strip():
                    page_content_map.setdefault(page_num, []).append(content)

        # 7. Slicing logic to safely guard against dense token limits
        for page_num in sorted(page_content_map.keys()):
            page_text = "\n".join(page_content_map[page_num]) + "\n"
            cleaned_page_text = clean_text(page_text)
            
            if cleaned_page_text.strip():
                if len(cleaned_page_text) <= 1200:
                    chunks_with_metadata.append({
                        "text": cleaned_page_text,
                        "index": page_num,
                        "source": path
                    })
                else:
                    sub_chunks = line_text_splitter(cleaned_page_text, CHUNK_SIZE)
                    for sub_chunk in sub_chunks:
                        if sub_chunk.strip():
                            chunks_with_metadata.append({
                                "text": sub_chunk,
                                "index": page_num,
                                "source": path
                            })

    except Exception as e:
        print(f"Modern Magic-PDF engine failed on document {filename}: {str(e)}")

    print(f"DOCUMENT {basename} chunking completed successfully! Generated {len(chunks_with_metadata)} chunks.")
    return chunks_with_metadata