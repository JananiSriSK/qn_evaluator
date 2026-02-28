import json
import faiss
from sentence_transformers import SentenceTransformer

# Load resources
encoder = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("vector_db/faiss_index.bin")

with open("vector_db/metadata.json", "r") as f:
    metadata = json.load(f)

with open("syllabus_enriched.json", "r") as f:
    syllabus = json.load(f)

# Test question
question = "explain why multiple inheritance is not applicable in java?"

# Find relevant chunks
q_emb = encoder.encode([question], convert_to_numpy=True).astype("float32")
faiss.normalize_L2(q_emb)
distances, indices = index.search(q_emb, 5)

print(f"Question: {question}\n")
print("Top 5 relevant chunks:")
for i, idx in enumerate(indices[0]):
    chunk = metadata[idx]
    print(f"\n{i+1}. Book: {chunk['book_name'][:50]}...")
    print(f"   Page: {chunk['page']}")
    print(f"   Text: {chunk['text'][:150]}...")

# Find matching topic
print("\n" + "="*80)
print("SYLLABUS MAPPING:")
print("="*80)

best_match = None
best_score = -1

for unit in syllabus["units"]:
    for topic in unit["topics"]:
        # Check if any source references match
        topic_chunks = [ref["chunk_id"] for ref in topic["source_references"]]
        overlap = len(set(indices[0]) & set(topic_chunks))
        
        if overlap > best_score:
            best_score = overlap
            best_match = {
                "unit": unit["unit_number"],
                "unit_title": unit["unit_title"],
                "topic": topic["topic_name"],
                "cos": topic["mapped_course_outcomes"],
                "subtopics": topic["enriched_subtopics_from_books"]
            }

if best_match:
    print(f"\nUnit: {best_match['unit']} - {best_match['unit_title']}")
    print(f"Topic: {best_match['topic']}")
    print(f"Course Outcomes: {', '.join(best_match['cos'])}")
    print(f"\nCO Details:")
    for co in best_match['cos']:
        print(f"  {co}: {syllabus['course_outcomes'][co]}")
    print(f"\nRelevant Subtopics:")
    for st in best_match['subtopics'][:5]:
        print(f"  - {st}")
else:
    print("\nNo matching topic found in syllabus")
