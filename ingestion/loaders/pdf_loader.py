"""PDF document loader."""
import os
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path

def get_pdf_file(path):
    pdf_reader = PdfReader(Path(path))
    filename = os.path.split(path)[-1]
    n_pages = len(pdf_reader.pages)
    return  pdf_reader, n_pages, filename


def chunk_pdf(path, out_dir, pages_per_chunk):
    pdf_reader, total_pages, filename = get_pdf_file(path)
    if pdf_reader is None:
        print(f"Impossible to read {path}")
        return
    
    try:
        basename = os.path.splitext(filename)[0] # leave .pdf out

        #Create or read folder path
        out_dir = Path(out_dir) 
        out_dir.mkdir(exist_ok=True)

        chunks_dir = Path(out_dir / basename)
        chunks_dir.mkdir(exist_ok=True)

        #Calculate n_chunks
        n_chunks = (total_pages + pages_per_chunk - 1) // pages_per_chunk #number of chunks
        print(f"Splitting {filename} with {total_pages} into {n_chunks} of {pages_per_chunk} each...")

        for i in range(n_chunks):
            writer = PdfWriter()
            start_page = i * pages_per_chunk
            end_page = min(start_page + pages_per_chunk, total_pages)

            print(f"Processing chunk {i+1}/{n_chunks} (pages {start_page-1}-{end_page})...")

            for page in range(start_page, end_page):
                writer.add_page(pdf_reader.pages[page])
            
            #Construct file chunk name
            out_filename = os.path.join(chunks_dir, f"chunk_{i+1}.pdf")

            #Write chunk
            with open(out_filename, 'wb') as f:
                writer.write(f)
            print(f"Chunk {i+1} saved as '{out_filename}'")
        
        print("\nPDF splitting completed successfully!")



    except Exception as e:
        print(f"Error encountered: {str(e)}")
