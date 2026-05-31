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
    Completely version-agnostic across py-tree-sitter property/method upgrades.
    """
    from tree_sitter_language_pack import get_parser
    parser = get_parser(language)
    
    try:
        tree = parser.parse(code)
    except TypeError:
        tree = parser.parse(code.encode('utf-8'))

    chunks = []

    # FIX: Resolve root node dynamically whether it's a property or a method
    if hasattr(tree, "root_node"):
        root = tree.root_node() if callable(tree.root_node) else tree.root_node
    else:
        return RecursiveSplitter(code, chunksize=1000, source=source)

    def visit(node):
        # Guardrail: protect against nulls or raw methods bleeding into the tree traversal
        if node is None or callable(node):
            return

        # FIX: Resolve type dynamically whether it's a property or a method
        try:
            node_type = node.type() if callable(node.type) else node.type
        except AttributeError:
            return

        interesting = {
            "function_definition",
            "method_definition",
            "class_definition",
            "function_declaration",
            "class_declaration",
        }

        if node_type in interesting:
            # Resolve text content cleanly
            if hasattr(node, "text"):
                chunk = node.text() if callable(node.text) else node.text
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8', errors='ignore')
            else:
                try:
                    start_byte = node.start_byte() if callable(node.start_byte) else node.start_byte
                    end_byte = node.end_byte() if callable(node.end_byte) else node.end_byte
                    chunk = code[start_byte:end_byte]
                except Exception:
                    chunk = str(node)

            chunks.append({
                "text": chunk,
                "index": len(chunks) + 1,
                "source": source
            })

        # FIX: Resolve children iteration dynamically whether it's a property or a method
        try:
            children = node.children() if callable(node.children) else node.children
            if children:
                for child in children:
                    visit(child)
        except Exception:
            pass

    visit(root)

    # Fallback for code files or flat scripts without formal class/function definitions
    if not chunks and code.strip():
        return RecursiveSplitter(code, chunksize=1000, source=source)

    return chunks