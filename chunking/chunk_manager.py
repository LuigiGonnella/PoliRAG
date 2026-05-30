"""Chunk management and strategy orchestration."""
import json
from langchain_text_splitters import (
    MarkdownTextSplitter, 
    RecursiveJsonSplitter, 
    CharacterTextSplitter, 
    PythonCodeTextSplitter, 
    NLTKTextSplitter, 
    RecursiveCharacterTextSplitter
)

def paragraph_splitter(text, chunksize, overlap, source=None):
    text_splitter = CharacterTextSplitter(separator="\n\n", chunk_size=chunksize, chunk_overlap=overlap)
    docs = text_splitter.create_documents([text])
    return [{"text": doc.page_content, "index": i + 1, "source": source} for i, doc in enumerate(docs)]

def newline_splitter(text, chunksize, overlap, source=None):
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=chunksize, chunk_overlap=overlap)
    docs = text_splitter.create_documents([text])
    return [{"text": doc.page_content, "index": i + 1, "source": source} for i, doc in enumerate(docs)]

def md_splitter(text, chunksize, overlap, source=None):
    text_splitter = MarkdownTextSplitter(chunk_size=chunksize, chunk_overlap=overlap)
    docs = text_splitter.create_documents([text])
    return [{"text": doc.page_content, "index": i + 1, "source": source} for i, doc in enumerate(docs)]

def json_splitter(text, chunksize, source=None):
    text_splitter = RecursiveJsonSplitter(max_chunk_size=chunksize)
    try:
        # FIX: Parse string into a valid nested Python structure before splitting
        json_data = json.loads(text)
        docs = text_splitter.create_documents(texts=[json_data])
        return [{"text": doc.page_content, "index": i + 1, "source": source} for i, doc in enumerate(docs)]
    except Exception as e:
        print(f"Warning: JSON parsing failed for {source}, falling back to RecursiveSplitter. Error: {e}")
        return RecursiveSplitter(text, chunksize, source)

def py_splitter(text, chunksize, overlap, source=None):
    text_splitter = PythonCodeTextSplitter(chunk_size=chunksize, chunk_overlap=overlap)
    docs = text_splitter.create_documents([text])
    return [{"text": doc.page_content, "index": i + 1, "source": source} for i, doc in enumerate(docs)]

def NLP_splitter(text, chunksize, source=None):
    splitter = NLTKTextSplitter(chunk_size=chunksize)
    # FIX: Wrap text inside a list format to avoid character-looping bugs
    docs = splitter.create_documents([text])
    return [{"text": doc.page_content, "index": i + 1, "source": source} for i, doc in enumerate(docs)]

def RecursiveSplitter(text, chunksize, source=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunksize,
        chunk_overlap=200 if chunksize > 200 else 50
    )
    docs = splitter.create_documents([text])
    return [{"text": doc.page_content, "index": i + 1, "source": source} for i, doc in enumerate(docs)]

def line_text_splitter(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """
    Splits input text into manageable string chunks based on character length 
    while respecting line boundaries to prevent cutting sentences in half.
    """
    if not text.strip():
        return []

    lines = text.splitlines()
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        line_len = len(line) + 1 
        
        if line_len > chunk_size:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            for i in range(0, len(line), chunk_size - overlap):
                chunks.append(line[i : i + chunk_size])
            continue

        if current_length + line_len > chunk_size:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            
            overlap_chunk = []
            overlap_len = 0
            for old_line in reversed(current_chunk):
                if overlap_len + len(old_line) + 1 <= overlap:
                    overlap_chunk.insert(0, old_line)
                    overlap_len += len(old_line) + 1
                else:
                    break
            
            current_chunk = overlap_chunk
            current_length = overlap_len

        current_chunk.append(line)
        current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def Treesitter_splitter(code: str, language: str, source=None):
    """
    Splits source code into logical, structural syntax blocks using Tree-Sitter.
    Safe against multi-byte characters and includes a recursive fallback for flat scripts.
    """
    from tree_sitter_language_pack import get_parser
    parser = get_parser(language)
    
    code_bytes = code.encode('utf-8')
    tree = parser.parse(code_bytes)

    chunks = []

    def visit(node):
        interesting = {
            "function_definition",
            "method_definition",
            "class_definition",
            "function_declaration",
            "class_declaration",
        }

        if node.type in interesting:
            # FIX: Slice using byte coordinates, then decode back safely to a Python string
            chunk = code_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
            chunks.append({
                "text": chunk,
                "index": len(chunks) + 1,
                "source": source
            })

        for child in node.children:
            visit(child)

    visit(tree.root_node)

    # GUARDRAIL: Fallback for scripts without formal functions/classes (e.g., casual scratchpads)
    if not chunks and code.strip():
        return RecursiveSplitter(code, chunksize=1000, source=source)

    return chunks