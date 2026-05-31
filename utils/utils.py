import os
from pathlib import Path

import os
from pathlib import Path

def scan(path):
    """
    Recursively generates absolute file paths within a directory tree.
    Bypasses heavy dependency environments, virtual folders, system assets,
    and specified useless/binary file extensions.
    """
    IGNORE_DIR_NAMES = {
        "venv", 
        ".venv", 
        "node_modules", 
        "__pycache__", 
        ".git", 
        ".idea", 
        ".vscode",
        "build",
        "dist"
    }
    
    IGNORE_FILE_NAMES = {"thumbs.db", "desktop.ini"}

    # Set of extensions to completely skip (must include the leading dot)
    IGNORE_EXTENSIONS = {
        # Machine Learning weights & checkpoints
        ".pth", ".pt", ".ckpt", ".safetensors", ".bin", ".onnx", 
        # Executables and system binaries
        ".exe", ".dll", ".so", ".dylib", 
        # Archives and compressed spaces
        ".zip", ".tar", ".gz", ".rar", ".7z", 
        # Media assets and system logs
        ".log", ".tmp", ".bak", ".png", ".jpg", ".jpeg", ".mp4"
    }

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                name_lower = entry.name.lower()
                
                # 1. Skip system hidden files, temporary locks, or explicit junk filenames
                if entry.name.startswith(('.', '~$')) or name_lower in IGNORE_FILE_NAMES:
                    continue
                    
                if entry.is_file():
                    # 2. Extract file extension and skip if it matches the ignore set
                    _, ext = os.path.splitext(name_lower)
                    if ext in IGNORE_EXTENSIONS:
                        continue
                    yield entry.path
                    
                elif entry.is_dir():
                    # 3. Short-circuit deep environments before stepping into them
                    if name_lower in IGNORE_DIR_NAMES:
                        continue
                    yield from scan(entry.path)
                    
    except PermissionError:
        print(f"Warning: Permission denied accessing system directory: {path}")
        
def extract_path_metadata(file_path, base_raw_dir):
    """
    Extractes educational hierarchical metadata layers dynamically 
    based on deterministic file path nesting levels.
    """
    path_obj = Path(file_path)
    base_obj = Path(base_raw_dir)
    
    try:
        relative_path = path_obj.relative_to(base_obj)
        parts = relative_path.parts
        
        # Unpack indices if they exist, protecting against loose base root files
        degree_level = parts[0] if len(parts) > 0 else "Unknown"
        year = parts[1] if len(parts) > 1 else "Unknown"         
        course = parts[2] if len(parts) > 2 else "Unknown"       
        
        return {
            "degree_level": degree_level,
            "year": year,
            "course": course
        }
    except Exception:
        return {"degree_level": "Unknown", "year": "Unknown", "course": "Unknown"}