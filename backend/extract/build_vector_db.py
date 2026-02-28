import json
import pickle
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF


class VectorDatabaseBuilder:

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(model_name)

    def extract_text(self, pdf_path):
        doc = fitz.open(pdf_path)
        pages = []

        for page_num in range(len(doc)):
            text = doc[page_num].get_text("text")
            if text.strip():
                pages.append((page_num, text))

        return pages

    def chunk_text(self, text, chunk_size=180, overlap=40):
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def build(self, docs_path="uploads", output_path="vector_db"):
        docs_path = Path(docs_path)
        output_path = Path(output_path)
        output_path.mkdir(exist_ok=True)

        pdf_files = list(docs_path.glob("*.pdf"))
        if not pdf_files:
            print("No PDFs found.")
            return

        all_chunks = []
        metadata = []
        chunk_id = 0

        for pdf in pdf_files:
            print(f"Processing {pdf.name}")
            pages = self.extract_text(pdf)

            for page_num, text in pages:
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

        print(f"Total chunks: {len(all_chunks)}")

        embeddings = self.embedder.encode(
            all_chunks,
            show_progress_bar=True,
            convert_to_numpy=True
        ).astype("float32")

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)

        faiss.normalize_L2(embeddings)
        index.add(embeddings)

        faiss.write_index(index, str(output_path / "faiss_index.bin"))

        with open(output_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print("Vector database built successfully.")


if __name__ == "__main__":
    builder = VectorDatabaseBuilder()
    builder.build()