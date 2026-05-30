"""PDF content parser using MinerU SDK."""
import os
import json
from mineru import MinerU
from cleaners.text_cleaner import clean_text

def chunk_pdf(path):
    """
    Get a path for a PDF file and returns CLEAN CHUNKS (1 page = 1 chunk) with content and metadata
    """
    chunks_with_metadata = []
    filename = os.path.split(path)[-1]
    basename = os.path.splitext(filename)[0]

    # Initialize the MinerU client 
    # (Pass token="your_token" if using their cloud precision API)
    parser = MinerU()

    print(f"Starting MinerU extraction for: {filename}")
    
    try:
        # 1. Request structural JSON to easily map content back to specific pages
        result_json_str = parser.extract(path, output_format='json')
        result_data = json.loads(result_json_str)
        
        # 2. Iterate through MinerU's native page-by-page structure
        pages = result_data.get("pages", [])
        for i, page in enumerate(pages):
            page_text_blocks = []
            
            for block in page.get("blocks", []):
                # MinerU handles text, formulas (LaTeX), and tables (as MD strings) out of the box
                if block.get("type") in ["text", "table", "formula", "title"]:
                    content = block.get("content", "") or block.get("text", "")
                    if content:
                        page_text_blocks.append(content)
            
            # Combine all structural blocks on this specific page
            page_text = "\n".join(page_text_blocks) + "\n"
            
            if page_text.strip():
                chunks_with_metadata.append({
                    "text": clean_text(page_text),
                    "index": i + 1,
                    "source": path
                })

    except Exception as e:
        print(f"Error during structural JSON extraction: {e}. Falling back to full markdown.")
        # Fallback to continuous markdown extract if layout mapping encounters an issue
        result = parser.extract(path, output_format='markdown')
        markdown_text = result.markdown if hasattr(result, 'markdown') else str(result)
        
        chunks_with_metadata.append({
            "text": clean_text(markdown_text),
            "index": 1,
            "source": path
        })

    print(f"DOCUMENT {basename} chunking retrieval completed successfully!")
    return chunks_with_metadata