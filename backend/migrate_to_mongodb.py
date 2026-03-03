"""
Migrate existing local data to MongoDB
Usage: python migrate_to_mongodb.py
"""

from services.mongodb_storage import MongoDBStorage
from pathlib import Path
import json
import faiss

def migrate_user_data(user_id: str):
    """Migrate all data for a user to MongoDB"""
    mongo = MongoDBStorage()
    user_path = Path("data") / user_id
    
    if not user_path.exists():
        print(f"❌ User {user_id} data not found")
        return
    
    print(f"[*] Migrating user {user_id} data to MongoDB...")
    
    # Migrate each domain
    for domain_path in user_path.iterdir():
        if not domain_path.is_dir():
            continue
        
        domain_name = domain_path.name
        print(f"\n  [+] Domain: {domain_name}")
        
        # Create domain
        mongo.create_domain(user_id, domain_name)
        
        # Migrate syllabus
        syllabus_json = domain_path / "syllabus.json"
        if syllabus_json.exists():
            with open(syllabus_json, 'r', encoding='utf-8') as f:
                syllabus_data = json.load(f)
            
            # Check for original file
            original_file = None
            filename = None
            for ext in ['.txt', '.pdf']:
                orig_path = domain_path / f"syllabus{ext}"
                if orig_path.exists():
                    with open(orig_path, 'rb') as f:
                        original_file = f.read()
                    filename = f"syllabus{ext}"
                    break
            
            mongo.save_syllabus(user_id, domain_name, syllabus_data, original_file, filename)
            print(f"    [OK] Syllabus migrated")
        
        # Migrate books
        books_path = domain_path / "books"
        if books_path.exists():
            for book_file in books_path.glob("*.pdf"):
                with open(book_file, 'rb') as f:
                    book_bytes = f.read()
                mongo.save_book(user_id, domain_name, book_bytes, book_file.name)
                print(f"    [OK] Book: {book_file.name}")
        
        # Migrate FAISS index
        index_path = domain_path / "vector_db" / "faiss_index.bin"
        metadata_path = domain_path / "vector_db" / "metadata.json"
        
        if index_path.exists() and metadata_path.exists():
            with open(index_path, 'rb') as f:
                index_bytes = f.read()
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            mongo.save_index(user_id, domain_name, index_bytes, metadata)
            print(f"    [OK] FAISS index migrated ({len(metadata)} chunks)")
    
    # Migrate history
    history_path = user_path / "history.json"
    if history_path.exists():
        with open(history_path, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        mongo.save_history(user_id, history_data)
        print(f"\n  [OK] History migrated")
    
    print(f"\n[SUCCESS] Migration complete for user {user_id}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = "1"  # Default
    
    print("=" * 60)
    print("  MongoDB Migration Tool")
    print("=" * 60)
    
    try:
        migrate_user_data(user_id)
        print("\n[SUCCESS] All data migrated successfully!")
        print("\nYou can now:")
        print("1. Open MongoDB Compass: mongodb://localhost:27017/")
        print("2. View database: qn_evaluator")
        print("3. Collections: syllabus, books, indexes, history")
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
