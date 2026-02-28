import json
import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

class EnrichmentService:
    """Enriches syllabus with subtopics using Groq LLM"""
    
    def __init__(self, groq_api_key=None):
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        self.groq_client = Groq(api_key=api_key)
    
    def enrich_syllabus(self, syllabus_path, index, metadata, bi_encoder, cross_encoder):
        """Enrich syllabus with subtopics from book chunks using Groq LLM"""
        
        with open(syllabus_path, "r") as f:
            syllabus = json.load(f)
        
        logger.info(f"Enriching syllabus with {len(metadata)} chunks...")
        
        for unit in syllabus["units"]:
            logger.info(f"Processing Unit {unit['unit_number']}: {unit['unit_title']}")
            
            for topic in unit["topics"]:
                topic_name = topic["topic_name"]
                logger.info(f"  - {topic_name}")
                
                # Retrieve and rerank
                candidates = self._retrieve_candidates(topic_name, index, metadata, bi_encoder, top_k=30)
                top_chunks = self._rerank(topic_name, candidates, cross_encoder, final_k=10)
                
                # Generate subtopics with Groq
                subtopics = self._generate_subtopics(topic_name, top_chunks)
                
                # Map course outcomes
                topic["mapped_course_outcomes"] = self._map_course_outcomes(unit["unit_number"])
                topic["enriched_subtopics_from_books"] = subtopics
                topic["source_references"] = [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "book_name": chunk["book_name"],
                        "page": chunk["page"]
                    }
                    for chunk in top_chunks
                ]
        
        # Save enriched syllabus
        with open(syllabus_path, "w") as f:
            json.dump(syllabus, f, indent=2)
        
        logger.info("✓ Syllabus enriched successfully")
        return syllabus
    
    def _retrieve_candidates(self, topic, index, metadata, bi_encoder, top_k=20):
        """Retrieve candidate chunks using bi-encoder"""
        import faiss
        
        embedding = bi_encoder.encode([topic], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(embedding)
        
        distances, indices = index.search(embedding, top_k)
        
        candidates = []
        for idx in indices[0]:
            if idx < len(metadata):
                candidates.append(metadata[idx])
        
        return candidates
    
    def _rerank(self, topic, candidates, cross_encoder, final_k=5):
        """Rerank candidates using cross-encoder"""
        pairs = [(topic, c["text"]) for c in candidates]
        scores = cross_encoder.predict(pairs)
        
        for i, score in enumerate(scores):
            candidates[i]["score"] = float(score)
        
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:final_k]
    
    def _generate_subtopics(self, topic_name, book_chunks):
        """Generate subtopics using Groq LLM"""
        context = "\n".join([f"- {chunk['text'][:300]}" for chunk in book_chunks])
        
        prompt = f"""Based on the topic '{topic_name}' and the following book content, generate 5-7 specific subtopics (not sentences, just topic names).

Book Content:
{context}

Generate subtopics as a JSON array of strings. Each subtopic should be a concise topic name (2-6 words), not a sentence.
Example format: ["Topic Name 1", "Topic Name 2", "Topic Name 3"]

Return ONLY the JSON array, nothing else."""
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            result = result.replace('```json', '').replace('```', '').strip()
            subtopics = json.loads(result)
            return subtopics[:7]
        except Exception as e:
            logger.warning(f"Groq generation failed: {e}, using fallback")
            return [chunk['text'][:80].strip() for chunk in book_chunks[:5]]
    
    def _map_course_outcomes(self, unit_number):
        """Map unit to course outcomes"""
        unit_co_map = {
            "I": ["CO1"],
            "II": ["CO2"],
            "III": ["CO3"],
            "IV": ["CO4"],
            "V": ["CO5"]
        }
        return unit_co_map.get(unit_number, [])
