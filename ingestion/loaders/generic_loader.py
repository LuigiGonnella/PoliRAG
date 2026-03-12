import os
from pathlib import Path
from chunking.chunk_manager import C_splitter, js_splitter, md_splitter, newline_splitter, py_splitter, java_splitter, json_splitter, line_text_splitter, paragraph_splitter, NLP_splitter

CHUNK_SIZE = 500
OVERLAP = 50

def get_generic_file(path):
    filename = os.path.split(path)[-1]
    return filename

def load_generic_text(path, out_dir):
    filename = get_generic_file(path)

    try:
        with open(path, 'r') as f:
            text = f.read()

        file_split = os.path.splitext(filename)
        basename = file_split[0]
        extension = file_split[1] #.txt, .C, .PY, ...

        #Create or read folder path
        out_dir = Path(out_dir) 
        out_dir.mkdir(exist_ok=True)

        chunks_dir = Path(out_dir / basename)
        chunks_dir.mkdir(exist_ok=True)

        if extension == "c":
            chunks = C_splitter(text)
        elif extension == "md":
            chunks = md_splitter(text, CHUNK_SIZE, OVERLAP)
        elif extension == "py":
            chunks = py_splitter(text, CHUNK_SIZE, OVERLAP)
        elif extension == "json":
            chunks = json_splitter(text, CHUNK_SIZE)
        elif extension == "js":
            chunks = js_splitter(text)
        elif extension == "java":
            chunks = java_splitter(text)
        else:
            chunks = NLP_splitter(text, CHUNK_SIZE)

    except Exception as e:
        print(f'Error encountered: {str(e)}')
    
    print(f"DOCUMENT {filename} chunking completed successfully!")
    return chunks

    