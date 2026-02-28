"""
Enrich syllabus with book references and map COs to units
Run this after uploading books to enable proper question mapping
"""

import json
from pathlib import Path
from services.domain_manager import DomainManager
from services.model_registry import model_registry
import numpy as np

def enrich_domain_syllabus(user_id, domain_name):
    """Enrich syllabus with book references and CO mapping"""
    
    # Load models
    print("Loading models...")
    model_registry.load_all_models()
    embedder = model_registry.get_bi_encoder()
    cross_encoder = model_registry.get_cross_encoder()
    
    # Load domain data
    dm = DomainManager("data", embedder=embedder)
    syllabus = dm.load_syllabus(user_id, domain_name)
    index, metadata = dm.load_index(user_id, domain_name)
    
    if not syllabus or not index:
        print("Error: Syllabus or index not found")
        return
    
    print(f"Enriching {domain_name} with {len(metadata)} chunks...")
    
    # Map COs to units (Unit I -> CO1, Unit II -> CO2, etc.)
    unit_to_co = {"I": ["CO1"], "II": ["CO2"], "III": ["CO3"], "IV": ["CO4"], "V": ["CO5"]}
    
    # Enrich each topic
    for unit in syllabus["units"]:
        unit_num = unit["unit_number"]
        print(f"\nProcessing Unit {unit_num}: {unit['unit_title']}")
        
        for topic in unit["topics"]:
            topic_name = topic["topic_name"]
            print(f"  - {topic_name}")
            
            # Map CO to topic
            topic["mapped_course_outcomes"] = unit_to_co.get(unit_num, [])
            
            # Find relevant chunks for this topic
            query = f"{unit['unit_title']} {topic_name}"
            query_emb = embedder.encode([query], convert_to_numpy=True).astype("float32")
            np.linalg.norm(query_emb, axis=1, keepdims=True)
            
            # Search FAISS
            scores, indices = index.search(query_emb, 20)
            
            # Get chunks
            candidates = []
            for idx, score in zip(indices[0], scores[0]):
                if idx < len(metadata):
                    chunk = metadata[idx]
                    candidates.append({
                        "text": chunk["text"],
                        "score": float(score),
                        "chunk_id": chunk["chunk_id"],
                        "book": chunk["book_name"],
                        "page": chunk["page"]
                    })
            
            # Rerank with cross-encoder
            if candidates:
                pairs = [[query, c["text"]] for c in candidates]
                rerank_scores = cross_encoder.predict(pairs)
                
                for i, score in enumerate(rerank_scores):
                    candidates[i]["rerank_score"] = float(score)
                
                # Sort by rerank score
                candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
                
                # Take top 5
                top_chunks = candidates[:5]
                
                # Add source references
                topic["source_references"] = [
                    {"chunk_id": c["chunk_id"], "book": c["book"], "page": c["page"]}
                    for c in top_chunks
                ]
                
                # Extract subtopics (simple: take first few words from top chunks)
                subtopics = []
                for c in top_chunks[:3]:
                    words = c["text"].split()[:15]
                    subtopic = " ".join(words)
                    if subtopic not in subtopics:
                        subtopics.append(subtopic)
                
                topic["enriched_subtopics_from_books"] = subtopics
    
    # Save enriched syllabus
    output_path = Path("data") / user_id / domain_name / "syllabus.json"
    with open(output_path, "w") as f:
        json.dump(syllabus, f, indent=2)
    
    print(f"\nEnriched syllabus saved to {output_path}")
    print(f"All topics now have CO mappings and book references")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python enrich_domain.py <user_id> <domain_name>")
        print("Example: python enrich_domain.py 1 JAVA_PROGRAMMING")
        sys.exit(1)
    
    user_id = sys.argv[1]
    domain_name = sys.argv[2]
    
    enrich_domain_syllabus(user_id, domain_name)
