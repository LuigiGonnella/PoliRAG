import os

def scan(path):
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                yield entry.path

            elif entry.is_dir():
                yield from scan(entry.path)
    
        
                

