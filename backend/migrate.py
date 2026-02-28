"""
Migration script: Move extract/ data to domain-based structure
"""
import shutil
from pathlib import Path
import json

def migrate_extract_to_domain():
    """Migrate existing extract/ data to domain structure"""
    
    # Source paths
    extract_path = Path("extract")
    uploads_path = extract_path / "uploads"
    vector_db_path = extract_path / "vector_db"
    syllabus_file = extract_path / "syllabus_enriched.json"
    
    # Target paths
    user_id = "default_user"
    domain_name = "JAVA_PROGRAMMING"
    target_path = Path(f"data/{user_id}/{domain_name}")
    target_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Migrating to: {target_path}")
    
    # 1. Copy syllabus
    if syllabus_file.exists():
        shutil.copy(syllabus_file, target_path / "syllabus.json")
        print("✓ Syllabus copied")
    
    # 2. Copy books
    if uploads_path.exists():
        target_books = target_path / "books"
        target_books.mkdir(exist_ok=True)
        
        for pdf in uploads_path.glob("*.pdf"):
            shutil.copy(pdf, target_books / pdf.name)
            print(f"✓ Book copied: {pdf.name}")
    
    # 3. Copy vector_db
    if vector_db_path.exists():
        target_vector = target_path / "vector_db"
        target_vector.mkdir(exist_ok=True)
        
        # Copy FAISS index
        if (vector_db_path / "faiss_index.bin").exists():
            shutil.copy(
                vector_db_path / "faiss_index.bin",
                target_vector / "faiss_index.bin"
            )
            print("✓ FAISS index copied")
        
        # Copy metadata
        if (vector_db_path / "metadata.json").exists():
            shutil.copy(
                vector_db_path / "metadata.json",
                target_vector / "metadata.json"
            )
            print("✓ Metadata copied")
    
    print(f"\n✓ Migration complete!")
    print(f"Domain: {user_id}/{domain_name}")
    print(f"Location: {target_path}")
    
    return user_id, domain_name

if __name__ == "__main__":
    migrate_extract_to_domain()
