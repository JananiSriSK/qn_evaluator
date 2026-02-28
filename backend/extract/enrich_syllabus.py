import json
import re
import os
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class SyllabusEnricher:

    def __init__(self):
        self.bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        self.index = faiss.read_index("vector_db/faiss_index.bin")
        
        with open("vector_db/metadata.json", "r") as f:
            self.metadata = json.load(f)

    # ---------------------------------------------------
    # STEP 1: CONVERT SYLLABUS TEXT TO JSON
    # ---------------------------------------------------
    def parse_syllabus_text(self, text_path="syllabus.txt"):

        with open(text_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = [line.strip() for line in content.split("\n") if line.strip()]

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

            # Topic line (topics separated by –)
            if current_unit and "–" in line:
                topics = [t.strip().strip(".") for t in line.split("–")]

                for topic in topics:
                    current_unit["topics"].append({
                        "topic_name": topic,
                        "mapped_course_outcomes": []
                    })

        if current_unit:
            syllabus["units"].append(current_unit)

        # Save structured syllabus
        with open("syllabus.json", "w") as f:
            json.dump(syllabus, f, indent=2)

        print("Syllabus converted to JSON successfully.")
        return syllabus

    # ---------------------------------------------------
    # RETRIEVAL
    # ---------------------------------------------------
    def retrieve_candidates(self, topic, top_k=20):
        embedding = self.bi_encoder.encode(
            [topic],
            convert_to_numpy=True
        ).astype("float32")

        faiss.normalize_L2(embedding)

        distances, indices = self.index.search(embedding, top_k)

        candidates = []
        for idx in indices[0]:
            candidates.append(self.metadata[idx])

        return candidates

    def rerank(self, topic, candidates, final_k=5):
        pairs = [(topic, c["text"]) for c in candidates]
        scores = self.cross_encoder.predict(pairs)

        for i, score in enumerate(scores):
            candidates[i]["score"] = float(score)

        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates[:final_k]

    def generate_subtopics_with_groq(self, topic_name, book_chunks):
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
        except:
            return [chunk['text'][:80].strip() for chunk in book_chunks[:5]]
    
    def map_course_outcomes(self, unit_number, topic_name, course_outcomes):
        unit_co_map = {
            "I": ["CO1"],
            "II": ["CO2"],
            "III": ["CO3"],
            "IV": ["CO4"],
            "V": ["CO5"]
        }
        return unit_co_map.get(unit_number, [])
    
    # ---------------------------------------------------
    # STEP 2: ENRICH SYLLABUS
    # ---------------------------------------------------
    def enrich(self, syllabus_path="syllabus.json"):

        with open(syllabus_path, "r") as f:
            syllabus = json.load(f)

        for unit in syllabus["units"]:
            print(f"\nProcessing Unit {unit['unit_number']}: {unit['unit_title']}")
            
            for topic in unit["topics"]:
                topic_name = topic["topic_name"]
                print(f"  - {topic_name}")
                
                candidates = self.retrieve_candidates(topic_name, top_k=30)
                top_chunks = self.rerank(topic_name, candidates, final_k=10)
                
                subtopics = self.generate_subtopics_with_groq(topic_name, top_chunks)
                
                topic["mapped_course_outcomes"] = self.map_course_outcomes(
                    unit["unit_number"], 
                    topic_name, 
                    syllabus.get("course_outcomes", {})
                )
                
                topic["enriched_subtopics_from_books"] = subtopics
                
                topic["source_references"] = [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "book_name": chunk["book_name"],
                        "page": chunk["page"]
                    }
                    for chunk in top_chunks
                ]

        with open("syllabus_enriched.json", "w") as f:
            json.dump(syllabus, f, indent=2)

        print("\nSyllabus enriched successfully.")


# ---------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------

if __name__ == "__main__":

    enricher = SyllabusEnricher()

    # Step 1: Convert syllabus.txt → syllabus.json
    enricher.parse_syllabus_text("syllabus.txt")

    # Step 2: Enrich
    enricher.enrich("syllabus.json")