"""Utility script to post-calculate and fix misaligned payload metadata fields in Qdrant."""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

def migrate_metadata():
    qdrant_url = os.environ.get("QDRANT_URL")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    collection_name = "uni_docs"

    if not qdrant_url or not qdrant_api_key:
        print("Error: Missing Qdrant credentials in environment.")
        return

    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    if not client.collection_exists(collection_name):
        print(f"Error: Collection '{collection_name}' not found.")
        return

    print("Connected to Qdrant Cloud. Scrolling points to fix metadata fields...")
    offset = None
    total_updated = 0

    while True:
        # Scroll through points in pages of 100 entries
        scroll_result, offset = client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        if not scroll_result:
            break

        operations = []
        for point in scroll_result:
            source_str = point.payload.get("source", "")
            if not source_str:
                continue

            # Standardize separators to process cross-platform path nesting levels smoothly
            normalized_path = source_str.replace("\\", "/")
            parts = [part for part in normalized_path.split("/") if part]

            if "Universita" in parts:
                uni_idx = parts.index("Universita")
                # Isolate everything down-tree from the base "Universita" directory boundary
                sub_tree = parts[uni_idx + 1:]
                
                # Default safety values
                degree_level = "Unknown"
                year = "Unknown"
                course = "Unknown"

                # Parse layout layers using relative list index checking
                if len(sub_tree) > 0:
                    degree_level = sub_tree[0]      # e.g., "Magistrale"
                if len(sub_tree) > 1:
                    year = sub_tree[1]              # e.g., "Secondo Anno"
                
                # Check if the third folder is the semester wrapper layer
                if len(sub_tree) > 2:
                    if "semestre" in sub_tree[2].lower():
                        # Shift depth index by 1 to isolate actual target course folder
                        course = sub_tree[3] if len(sub_tree) > 3 else "Unknown"
                    else:
                        course = sub_tree[2]

                # Verify if values changed from the stored attributes to minimize write transactions
                current_course = point.payload.get("course")
                current_degree = point.payload.get("degree_level")
                current_year = point.payload.get("year")

                if (course != current_course) or (degree_level != current_degree) or (year != current_year):
                    new_metadata = {
                        "degree_level": degree_level,
                        "year": year,
                        "course": course
                    }
                    
                    # Queue the point update payload action
                    operations.append(
                        models.SetPayloadOperation(
                            set_payload=models.SetPayload(
                                payload=new_metadata,
                                points=[point.id]
                            )
                        )
                    )

        # Batch-upload point corrections to minimize roundtrips
        if operations:
            client.batch_update_points(
                collection_name=collection_name,
                update_operations=operations,
                wait=True
            )
            total_updated += len(operations)
            print(f"Corrected metadata for a batch of {len(operations)} entries. (Total: {total_updated})")

        if offset is None:
            break

    print(f"\nSuccess! Fixed structural metadata fields for {total_updated} points in your cloud cluster.")

if __name__ == "__main__":
    migrate_metadata()