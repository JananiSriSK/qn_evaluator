import json
import shutil
from pathlib import Path
import fitz
import faiss
import re
import logging

logger = logging.getLogger(__name__)


class DomainManager:
    """Manages domain-based storage and FAISS indices"""
    
    def __init__(self, base_path="data", embedder=None):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self._embedder = embedder
    
    def get_domain_path(self, user_id, domain_name):
        """Get path for specific domain"""
        path = self.base_path / user_id / domain_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_books_path(self, user_id, domain_name):
        """Get books directory for domain"""
        path = self.get_domain_path(user_id, domain_name) / "books"
        path.mkdir(exist_ok=True)
        return path
    
    def get_vector_db_path(self, user_id, domain_name):
        """Get vector_db directory for domain"""
        path = self.get_domain_path(user_id, domain_name) / "vector_db"
        path.mkdir(exist_ok=True)
        return path
    
    def load_index(self, user_id, domain_name):
        """Load FAISS index and metadata for domain"""
        vector_path = self.get_vector_db_path(user_id, domain_name)
        index_file = vector_path / "faiss_index.bin"
        metadata_file = vector_path / "metadata.json"
        
        if not index_file.exists() or not metadata_file.exists():
            return None, None
        
        index = faiss.read_index(str(index_file))
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        return index, metadata
    
    def load_syllabus(self, user_id, domain_name):
        """Load syllabus.json for domain"""
        syllabus_file = self.get_domain_path(user_id, domain_name) / "syllabus.json"
        
        if not syllabus_file.exists():
            return None
        
        with open(syllabus_file, "r") as f:
            return json.load(f)
    
    def parse_syllabus_text(self, text):
        """Parse syllabus text into structured JSON"""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        syllabus = {
            "course_name": lines[0],
            "units": [],
            "course_outcomes": {}
        }
        
        current_unit = None
        
        for line in lines[1:]:
            # UNIT detection
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
            
            # Course Outcomes
            co_match = re.match(r"(CO\d+):\s+(.*)", line)
            if co_match:
                syllabus["course_outcomes"][co_match.group(1)] = co_match.group(2)
                continue
            
            # Topics
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
    
    def save_syllabus(self, user_id, domain_name, file_path):
        """Save and parse syllabus file (PDF or TXT)"""
        file_path = Path(file_path)
        domain_path = self.get_domain_path(user_id, domain_name)
        
        # Save original file
        original_dest = domain_path / f"syllabus{file_path.suffix}"
        shutil.copy(file_path, original_dest)
        
        # Extract text
        if file_path.suffix.lower() == ".pdf":
            doc = fitz.open(file_path)
            text = "\n".join([page.get_text() for page in doc])
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        
        # Parse
        syllabus = self.parse_syllabus_text(text)
        
        # Save parsed JSON
        with open(domain_path / "syllabus.json", "w") as f:
            json.dump(syllabus, f, indent=2)
        
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
        """Build FAISS index from books in domain"""
        if embedder is None and self._embedder is None:
            raise RuntimeError("Embedder not provided. Pass from model_registry.")
        
        embedder = embedder or self._embedder
        
        books_path = self.get_books_path(user_id, domain_name)
        vector_path = self.get_vector_db_path(user_id, domain_name)
        
        pdf_files = list(books_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {books_path}")
            return False
        
        logger.info(f"Building index for {len(pdf_files)} books...")
        
        all_chunks = []
        metadata = []
        chunk_id = 0
        
        for pdf in pdf_files:
            logger.info(f"Processing: {pdf.name}")
            doc = fitz.open(pdf)
            
            for page_num in range(len(doc)):
                text = doc[page_num].get_text("text")
                if not text.strip():
                    continue
                
                chunks = self.chunk_text(text)
                
                for chunk in chunks:
                    all_chunks.append(chunk)
                    metadata.append({
                        "chunk_id": chunk_id,
                        "book_name": pdf.name,
                        "page": page_num,
                        "text": chunk
                    })
                    chunk_id += 1
        
        if not all_chunks:
            logger.warning("No chunks extracted from books")
            return False
        
        logger.info(f"Total chunks: {len(all_chunks)}")
        
        # Build FAISS index using provided embedder
        embeddings = embedder.encode(
            all_chunks,
            show_progress_bar=False,
            convert_to_numpy=True
        ).astype("float32")
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        
        # Save
        faiss.write_index(index, str(vector_path / "faiss_index.bin"))
        
        with open(vector_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✓ Index built: {index.ntotal} vectors")
        return True
    
    def add_books(self, user_id, domain_name, book_files, embedder=None):
        """Add books to domain and rebuild index"""
        books_path = self.get_books_path(user_id, domain_name)
        
        for book_file in book_files:
            dest = books_path / Path(book_file).name
            shutil.copy(book_file, dest)
        
        return self.build_vector_db(user_id, domain_name, embedder)
