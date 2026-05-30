"""Generic code and plaintext document file loader."""
import os
from pathlib import Path
from chunking.chunk_manager import (
    md_splitter, py_splitter, json_splitter, 
    RecursiveSplitter, NLP_splitter, Treesitter_splitter
)

CHUNK_SIZE = 1000
OVERLAP = 50

def chunk_generic_text(path):
    filename = os.path.basename(path)
    chunks_with_metadata = []

    try:
        # Avoid charset parsing crashes on non-ASCII characters inside old source files
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # FIX: Strip leading dot characters to guarantee match conditions trigger correctly
        extension = os.path.splitext(filename)[1].lower().lstrip('.')

        # Route text content to specialized syntactic splitters
        if extension == "c":
            raw_chunks = Treesitter_splitter(text, language="c", source=path)
        elif extension == "md":
            raw_chunks = md_splitter(text, CHUNK_SIZE, OVERLAP, source=path)
        elif extension == "py":
            raw_chunks = py_splitter(text, CHUNK_SIZE, OVERLAP, source=path)
        elif extension == "json":
            raw_chunks = json_splitter(text, CHUNK_SIZE, source=path)
        elif extension == "js":
            raw_chunks = Treesitter_splitter(text, language="javascript", source=path)
        elif extension == "java":
            raw_chunks = Treesitter_splitter(text, language="java", source=path)
        elif extension == "txt":
            raw_chunks = NLP_splitter(text, CHUNK_SIZE, source=path)
        else:
            raw_chunks = RecursiveSplitter(text, CHUNK_SIZE, source=path)

        # Format output structures cleanly into your standard metadata schemas
        if raw_chunks and isinstance(raw_chunks, list):
            for idx, chunk in enumerate(raw_chunks):
                if isinstance(chunk, dict):
                    chunks_with_metadata.append(chunk)
                else:
                    chunks_with_metadata.append({
                        "text": str(chunk),
                        "index": idx + 1,
                        "source": path
                    })

    except Exception as e:
        print(f"Error encountered processing generic file {filename}: {str(e)}")
    
    print(f"DOCUMENT {filename} chunking completed successfully! Created {len(chunks_with_metadata)} chunks.")
    return chunks_with_metadata