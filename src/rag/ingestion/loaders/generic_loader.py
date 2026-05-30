import os
from pathlib import Path
from chunking.chunk_manager import C_splitter, js_splitter, md_splitter, newline_splitter, py_splitter, java_splitter, json_splitter, line_text_splitter, paragraph_splitter, NLP_splitter


CHUNK_SIZE = 500
OVERLAP = 50

def get_generic_file(path):
    filename = os.path.split(path)[-1]
    return filename

def chunk_generic_text(path):
    filename = get_generic_file(path)

    try:
        with open(path, 'r') as f:
            text = f.read()

        file_split = os.path.splitext(filename)
        extension = file_split[1] #.txt, .C, .PY, ...

        if extension == "c":
            chunks = C_splitter(text, source=path)
        elif extension == "md":
            chunks = md_splitter(text, CHUNK_SIZE, OVERLAP, source=path)
        elif extension == "py":
            chunks = py_splitter(text, CHUNK_SIZE, OVERLAP, source=path)
        elif extension == "json":
            chunks = json_splitter(text, CHUNK_SIZE, source=path)
        elif extension == "js":
            chunks = js_splitter(text, source=path)
        elif extension == "java":
            chunks = java_splitter(text, source=path)
        elif extension == "txt":
            chunks = NLP_splitter(text, CHUNK_SIZE, source=path)
        else:
            chunks = None

    
        

    except Exception as e:
        print(f'Error encountered: {str(e)}')
    
    print(f"DOCUMENT {filename} chunking completed successfully!")
    return chunks

    