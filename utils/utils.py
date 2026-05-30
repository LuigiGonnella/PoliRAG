import os
from pathlib import Path

def scan(path):
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                yield entry.path

            elif entry.is_dir():
                yield from scan(entry.path)


def extract_path_metadata(file_path, base_raw_dir):
    path_obj = Path(file_path)
    
    try:
        # Get the path relative to your raw data folder
        # e.g., 'Triennale/Primo Anno/Chimica/Capitolo 01.pdf'
        relative_path = path_obj.relative_to(base_raw_dir)
        parts = relative_path.parts
        
        # Safe unpacking based on your directory layout
        degree_level = parts[0] if len(parts) > 0 else "Unknown"
        year = parts[1] if len(parts) > 2 else "Unknown"  # e.g., "Primo Anno"
        course = parts[2] if len(parts) > 3 else "Unknown" # e.g., "Chimica"
        
        return {
            "degree_level": degree_level,
            "year": year,
            "course": course
        }
    except Exception:
        # Fallback if a file sits outside the raw folder structure
        return {"degree_level": "Unknown", "year": "Unknown", "course": "Unknown"}
    
        
                

