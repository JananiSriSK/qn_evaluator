"""
Migrate local filesystem data to MongoDB
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.mongodb_storage import MongoDBStorage

def migrate_domain(user_id: str, domain_name: str):
    """Migrate a single domain from local to MongoDB"""
    mongo = MongoDBStorage()
    domain_path = Path("data") / user_id / domain_name
    
    if not domain_path.exists():
        print(f"[X] Domain not found: {domain_path}")
        return False
    
    print(f"\n[*] Migrating {user_id}/{domain_name}...")
    
    # 1. Create domain entry
    try:
        mongo.create_domain(user_id, domain_name)
        print(f"  [OK] Domain entry created")
    except Exception as e:
        print(f"  [X] Domain creation failed: {e}")
        return False
    
    # 2. Migrate syllabus
    syllabus_json = domain_path / "syllabus.json"
    syllabus_txt = domain_path / "syllabus.txt"
    
    if syllabus_json.exists():
        try:
            with open(syllabus_json, 'r', encoding='utf-8') as f:
                syllabus_data = json.load(f)
            
            # Get original file if exists
            original_file = None
            filename = None
            if syllabus_txt.exists():
                with open(syllabus_txt, 'rb') as f:
                    original_file = f.read()
                filename = "syllabus.txt"
            
            mongo.save_syllabus(user_id, domain_name, syllabus_data, original_file, filename)
            print(f"  [OK] Syllabus migrated")
        except Exception as e:
            print(f"  [X] Syllabus migration failed: {e}")
    else:
        print(f"  [!] No syllabus found")
    
    # 3. Migrate books
    books_path = domain_path / "books"
    if books_path.exists():
        book_files = list(books_path.glob("*.pdf"))
        for book_file in book_files:
            try:
                with open(book_file, 'rb') as f:
                    book_bytes = f.read()
                mongo.save_book(user_id, domain_name, book_bytes, book_file.name)
                print(f"  [OK] Book migrated: {book_file.name}")
            except Exception as e:
                print(f"  [X] Book migration failed ({book_file.name}): {e}")
    else:
        print(f"  [!] No books found")
    
    # 4. Migrate FAISS index
    index_path = domain_path / "vector_db" / "faiss_index.bin"
    metadata_path = domain_path / "vector_db" / "metadata.json"
    
    if index_path.exists() and metadata_path.exists():
        try:
            with open(index_path, 'rb') as f:
                index_bytes = f.read()
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            mongo.save_index(user_id, domain_name, index_bytes, metadata)
            print(f"  [OK] FAISS index migrated ({len(metadata)} chunks)")
        except Exception as e:
            print(f"  [X] Index migration failed: {e}")
    else:
        print(f"  [!] No FAISS index found")
    
    print(f"[DONE] Migration completed for {domain_name}\n")
    return True

if __name__ == "__main__":
    # Migrate JAVA PROG domain
    migrate_domain("1", "JAVA PROG")
