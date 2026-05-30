import os
from pathlib import Path

def scan(path):
    """
    Recursively generates absolute file paths within a directory tree.
    Skips hidden operating system files and configuration directories.
    """
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                # Defensive check: Ignore hidden files/folders (.DS_Store, .git, temporary locks)
                if entry.name.startswith('.' or '~$') or entry.name.lower() == 'thumbs.db':
                    continue
                    
                if entry.is_file():
                    yield entry.path
                elif entry.is_dir():
                    yield from scan(entry.path)
    except PermissionError:
        # Resilient handling for system-protected or locked directories
        print(f"Warning: Permission denied accessing system directory: {path}")

def extract_path_metadata(file_path, base_raw_dir):
    """
    Extracts educational hierarchical metadata layers dynamically 
    based on deterministic file path nesting levels.
    """
    path_obj = Path(file_path)
    base_obj = Path(base_raw_dir)
    
    try:
        # Extract path relative to your raw data root folder
        relative_path = path_obj.relative_to(base_obj)
        parts = relative_path.parts
        
        # Safe unpacking protecting against loose intermediate files
        degree_level = parts[0] if len(parts) > 0 else "Unknown"
        year = parts[1] if len(parts) > 2 else "Unknown"         # e.g., "Primo Anno"
        course = parts[2] if len(parts) > 3 else "Unknown"       # e.g., "Chimica"
        
        return {
            "degree_level": degree_level,
            "year": year,
            "course": course
        }
    except Exception:
        # Safe fallback boundary if a manual execution occurs outside your target root
        return {"degree_level": "Unknown", "year": "Unknown", "course": "Unknown"}