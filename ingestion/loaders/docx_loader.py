"""PDF document loader."""
from docx import Document
from pathlib import Path
from typing import List
import os

from chunking.chunk_manager import line_text_splitter

CHUNK_SIZE = 500


def get_docx_file(path):
    filename = os.path.split(path)[-1]
    doc = Document(Path(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
    
    text ="\n".join(parts)
    return text, filename
    

def chunk_docx(path, out_dir):
    try:
        text, filename = get_docx_file(path)
        basename = os.path.splitext(filename)[0] # leave .XXX out

        #Create or read folder path
        out_dir = Path(out_dir) 
        out_dir.mkdir(exist_ok=True)

        chunks_dir = Path(out_dir / basename)
        chunks_dir.mkdir(exist_ok=True)

        chunks = line_text_splitter(text, CHUNK_SIZE)

    except Exception as e:
        print(f"Error encountered: {str(e)}")

    print(f"DOCUMENT {filename} chunking completed successfully!")

    return chunks