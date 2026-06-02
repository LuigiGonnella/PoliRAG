"""Jupyter Notebook structural cell parsing and window chunking routine."""
import json

def chunk_ipynb(file_path, chunk_size=500, chunk_overlap=50):
    """
    Parses notebook JSON structures, formatting markdown prose and wrapping 
    source code inputs into markdown syntax code blocks before building chunks.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON from notebook [{file_path}]: {e}")
        return []

    cells = notebook_data.get("cells", [])
    processed_elements = []

    # 1. Iterate through notebook components sequentially
    for cell_idx, cell in enumerate(cells):
        cell_type = cell.get("cell_type")
        source_lines = cell.get("source", [])
        
        # Convert list of string lines into a single string block
        cell_text = "".join(source_lines).strip()
        if not cell_text:
            continue

        if cell_type == "markdown":
            # Append markdown directly
            processed_elements.append(cell_text)
            
        elif cell_type == "code":
            # Format code sections using clean Markdown syntactic wrappers
            formatted_code = f"```python\n# [Cell {cell_idx + 1}]\n{cell_text}\n```"
            processed_elements.append(formatted_code)

    # Combine everything into a single layout space
    full_document_text = "\n\n".join(processed_elements)
    words = full_document_text.split()
    
    chunks = []
    chunk_index = 0
    
    # 2. Slice text layout into overlapping semantic search windows
    i = 0
    while i < len(words):
        window_words = words[i:i + chunk_size]
        if not window_words:
            break
            
        chunk_text = " ".join(window_words)
        chunks.append({
            "text": chunk_text,
            "source": file_path,
            "index": chunk_index
        })
        
        chunk_index += 1
        i += (chunk_size - chunk_overlap)
        
    return chunks