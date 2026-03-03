import json
import io
import fitz
import faiss
import re
import logging
import numpy as np

logger = logging.getLogger(__name__)


class DomainManager:
    """Manages domain-based storage using MongoDB only"""
    
    def __init__(self, base_path="data", embedder=None, mongo_storage=None):
        self._embedder = embedder
        self.mongo_storage = mongo_storage
        if not mongo_storage:
            raise RuntimeError("MongoDB storage is required")
    
    def load_index(self, user_id, domain_name):
        """Load FAISS index and metadata from MongoDB"""
        index_bytes, metadata = self.mongo_storage.get_index(user_id, domain_name)
        
        if not index_bytes or not metadata:
            return None, None
        
        # Deserialize FAISS index from bytes
        index = faiss.deserialize_index(np.frombuffer(index_bytes, dtype='uint8'))
        return index, metadata
    
    def load_syllabus(self, user_id, domain_name):
        """Load syllabus from MongoDB"""
        return self.mongo_storage.get_syllabus(user_id, domain_name)
    
    def parse_syllabus_text(self, text):
        """Parse syllabus text into structured JSON"""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        syllabus = {
            "course_name": lines[0] if lines else "Unknown Course",
            "units": [],
            "course_outcomes": {}
        }
        
        current_unit = None
        
        for line in lines[1:]:
            unit_match = re.match(r"UNIT\s+([IVXLC]+)\s+(.*)", line)
            if unit_match:
                if current_unit:
                    syllabus["units"].append(current_unit)
                
                current_unit = {
                    "unit_number": unit_match.group(1),
                    "unit_title": unit_match.group(2).strip(),
                    "topics": []
                }
                continue
            
            co_match = re.match(r"(CO\d+):\s+(.*)", line)
            if co_match:
                syllabus["course_outcomes"][co_match.group(1)] = co_match.group(2)
                continue
            
            if current_unit and "–" in line:
                topics = [t.strip().strip(".") for t in line.split("–")]
                for topic in topics:
                    current_unit["topics"].append({
                        "topic_name": topic,
                        "mapped_course_outcomes": []
                    })
        
        if current_unit:
            syllabus["units"].append(current_unit)
        
        return syllabus
    
    def save_syllabus(self, user_id, domain_name, file_bytes, filename):
        """Save and parse syllabus file to MongoDB"""
        # Extract text
        if filename.lower().endswith(".pdf"):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = "\n".join([page.get_text() for page in doc])
        else:
            text = file_bytes.decode('utf-8')
        
        # Parse
        syllabus = self.parse_syllabus_text(text)
        
        # Save to MongoDB
        result = self.mongo_storage.save_syllabus(user_id, domain_name, syllabus, file_bytes, filename)
        logger.info(f"MongoDB write → collection=syllabus, user_id={user_id}, domain={domain_name}")
        
        return syllabus
    
    def chunk_text(self, text, chunk_size=180, overlap=40):
        """Chunk text into overlapping segments"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def build_vector_db(self, user_id, domain_name, embedder=None):
        """Build FAISS index from books in MongoDB"""
        if embedder is None and self._embedder is None:
            raise RuntimeError("Embedder not provided")
        
        embedder = embedder or self._embedder
        
        book_names = self.mongo_storage.list_books(user_id, domain_name)
        if not book_names:
            logger.warning(f"No books found for {user_id}/{domain_name}")
            return False
        
        logger.info(f"Building index for {len(book_names)} books...")
        
        all_chunks = []
        metadata = []
        chunk_id = 0
        
        for book_name in book_names:
            logger.info(f"Processing: {book_name}")
            book_bytes = self.mongo_storage.get_book(user_id, domain_name, book_name)
            
            if not book_bytes:
                continue
            
            doc = fitz.open(stream=book_bytes, filetype="pdf")
            
            for page_num in range(len(doc)):
                text = doc[page_num].get_text("text")
                if not text.strip():
                    continue
                
                chunks = self.chunk_text(text)
                
                for chunk in chunks:
                    all_chunks.append(chunk)
                    metadata.append({
                        "chunk_id": chunk_id,
                        "book_name": book_name,
                        "page": page_num,
                        "text": chunk
                    })
                    chunk_id += 1
        
        if not all_chunks:
            logger.warning("No chunks extracted from books")
            return False
        
        logger.info(f"Total chunks: {len(all_chunks)}")
        
        # Build FAISS index
        embeddings = embedder.encode(
            all_chunks,
            show_progress_bar=False,
            convert_to_numpy=True
        ).astype("float32")
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        
        # Serialize FAISS index to bytes
        index_bytes = faiss.serialize_index(index).tobytes()
        
        # Save to MongoDB
        self.mongo_storage.save_index(user_id, domain_name, index_bytes, metadata)
        logger.info(f"MongoDB write → collection=indexes, user_id={user_id}, domain={domain_name}, vectors={index.ntotal}")
        
        return True
    
    def add_books(self, user_id, domain_name, book_files, embedder=None):
        """Add books to MongoDB and rebuild index"""
        for book_file in book_files:
            with open(book_file, 'rb') as f:
                book_bytes = f.read()
            
            filename = book_file.name if hasattr(book_file, 'name') else str(book_file).split('/')[-1]
            self.mongo_storage.save_book(user_id, domain_name, book_bytes, filename)
            logger.info(f"MongoDB write → collection=books, user_id={user_id}, domain={domain_name}, file={filename}")
        
        return self.build_vector_db(user_id, domain_name, embedder)
