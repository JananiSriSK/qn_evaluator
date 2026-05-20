"""
Migrate all data from local MongoDB to MongoDB Atlas.
Run from backend/ directory: python migrate_to_atlas.py
"""
from pymongo import MongoClient
import gridfs

LOCAL_URI = "mongodb://localhost:27017/"
ATLAS_URI = "mongodb+srv://skjananisri_db_user:TSvdw8j1AzDJxZLZ@cluster0.jbirktb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "qn_evaluator"

def migrate():
    print("Connecting to local MongoDB...")
    local_client = MongoClient(LOCAL_URI)
    local_db = local_client[DB_NAME]

    print("Connecting to MongoDB Atlas...")
    atlas_client = MongoClient(ATLAS_URI)
    atlas_db = atlas_client[DB_NAME]

    # Migrate regular collections
    collections = ["domains", "syllabus", "books", "indexes", "history"]
    for col in collections:
        docs = list(local_db[col].find({}))
        if not docs:
            print(f"  {col}: empty, skipping")
            continue
        # Remove _id to avoid duplicate key errors, Atlas will generate new ones
        for doc in docs:
            doc.pop("_id", None)
        atlas_db[col].delete_many({})  # clear existing
        atlas_db[col].insert_many(docs)
        print(f"  {col}: migrated {len(docs)} documents")

    # Migrate GridFS files
    print("Migrating GridFS files...")
    local_fs = gridfs.GridFS(local_db)
    atlas_fs = gridfs.GridFS(atlas_db)

    # Clear existing GridFS in Atlas
    for f in atlas_db["fs.files"].find({}):
        try:
            atlas_fs.delete(f["_id"])
        except Exception:
            pass

    files = list(local_db["fs.files"].find({}))
    print(f"  Found {len(files)} GridFS files")
    for file_doc in files:
        try:
            local_file = local_fs.get(file_doc["_id"])
            data = local_file.read()
            metadata = {k: v for k, v in file_doc.items()
                       if k not in ("_id", "length", "chunkSize", "uploadDate", "md5", "filename")}
            atlas_fs.put(data, filename=file_doc.get("filename", "unknown"), **metadata)
            print(f"    Migrated: {file_doc.get('filename', 'unknown')} ({len(data)} bytes)")
        except Exception as e:
            print(f"    Failed: {file_doc.get('filename', '?')} — {e}")

    print("\nMigration complete!")
    local_client.close()
    atlas_client.close()

if __name__ == "__main__":
    migrate()
