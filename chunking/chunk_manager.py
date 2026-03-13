"""Chunk management and strategy orchestration."""
from langchain_text_splitters import MarkdownTextSplitter, RecursiveJsonSplitter, CharacterTextSplitter, PythonCodeTextSplitter, NLTKTextSplitter
import re

def paragraph_splitter(text, chunksize, overlap, source=None):
    text_splitter = CharacterTextSplitter(separator="\n\n", chunk_size = chunksize, chunk_overlap = overlap)
    docs = text_splitter.create_documents([text])
    chunks_with_metadata = [{"text": doc.page_content, "index": i, "source": source} for i, doc in enumerate(docs)]

    return chunks_with_metadata

def newline_splitter(text, chunksize, overlap, source=None):
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size = chunksize, chunk_overlap = overlap)
    docs = text_splitter.create_documents([text])
    chunks_with_metadata = [{"text": doc.page_content, "index": i, "source": source} for i, doc in enumerate(docs)]

    return chunks_with_metadata

def md_splitter(text, chunksize, overlap, source=None):
    text_splitter = MarkdownTextSplitter(chunk_size = chunksize, chunk_overlap = overlap)
    docs = text_splitter.create_documents([text])
    chunks_with_metadata = [{"text": doc.page_content, "index": i, "source": source} for i, doc in enumerate(docs)]

    return chunks_with_metadata

def json_splitter(text, chunksize, source=None):
    text_splitter = RecursiveJsonSplitter(max_chunk_size=chunksize)
    docs = text_splitter.create_documents([text])
    chunks_with_metadata = [{"text": doc.page_content, "index": i, "source": source} for i, doc in enumerate(docs)]

    return chunks_with_metadata

def py_splitter(text, chunksize, overlap, source=None):
    text_splitter = PythonCodeTextSplitter(chunk_size = chunksize, chunk_overlap = overlap)
    docs = text_splitter.create_documents([text])
    chunks_with_metadata = [{"text": doc.page_content, "index": i, "source": source} for i, doc in enumerate(docs)]

    return chunks_with_metadata


def js_splitter(code_text, overlap=2, source=None):
    """
    Splits JS code into function-level chunks.
    overlap: number of previous lines to include for context
    """
    # Find all function and class definitions
    pattern = re.compile(r'^(function\s+\w+|\w+\s*=\s*function|\w+\s*\(.*\))', re.MULTILINE)
    matches = list(pattern.finditer(code_text))
    
    chunks = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(code_text)
        chunk_lines = code_text[start:end].splitlines()

        if i > 0 and overlap > 0:
            prev_chunk_lines = code_text[matches[i-1].start():start].splitlines()
            chunk_lines = prev_chunk_lines[-overlap:] + chunk_lines

        chunk = "\n".join(chunk_lines)
        chunks.append({"text": chunk, "index": i, "source": source})

    return chunks

def java_splitter(code_text, overlap=2, source=None):
    """
    Splits JS code into function-level chunks.
    overlap: number of previous lines to include for context
    """
    # Find all function and class definitions
    pattern = re.compile(r'^\s*(public|private|protected|static|\s)*\s*\w+(\<.*\>)?\s+\w+\s*\(.*\)\s*\{', re.MULTILINE)
    matches = list(pattern.finditer(code_text))
    
    chunks = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(code_text)
        chunk_lines = code_text[start:end].splitlines()

        if i > 0 and overlap > 0:
            prev_chunk_lines = code_text[matches[i-1].start():start].splitlines()
            chunk_lines = prev_chunk_lines[-overlap:] + chunk_lines

        chunk = "\n".join(chunk_lines)
        chunks.append({"text": chunk, "index": i, "source": source})

    return chunks

def C_splitter(code_text, overlap=2, source=None):
    """
    Splits JS code into function-level chunks.
    overlap: number of previous lines to include for context
    """
    # Find all function and class definitions
    pattern = re.compile(r'^\s*(?:\w+\s+)+\w+\s*\(.*\)\s*\{ ', re.MULTILINE)
    matches = list(pattern.finditer(code_text))
    
    chunks = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(code_text)
        chunk_lines = code_text[start:end].splitlines()

        if i > 0 and overlap > 0:
            prev_chunk_lines = code_text[matches[i-1].start():start].splitlines()
            chunk_lines = prev_chunk_lines[-overlap:] + chunk_lines

        chunk = "\n".join(chunk_lines)
        chunks.append({"text": chunk, "index": i, "source": source})

    return chunks

def line_text_splitter(text, chunk_size, overlap = 5, source=None):
    lines = text.splitlines()
    chunks = []

    for i in range(0, len(lines), chunk_size - overlap):
        chunk = "\n".join(lines[i : i + chunk_size])
        chunks.append({"text": chunk, "index": i // (chunk_size - overlap), "source": source})

    return chunks

def NLP_splitter(text, chunksize, source):
    splitter = NLTKTextSplitter(chunk_size = chunksize)
    docs = splitter.create_documents(text)
    chunks_with_metadata = [{"text": doc.page_content, "index": i, "source": source} for i, doc in enumerate(docs)]

    return chunks_with_metadata
