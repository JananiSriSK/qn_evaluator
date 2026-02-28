"""
Test script for new domain-based architecture
"""
import sys
sys.path.append('backend')

from services.domain_manager import DomainManager
from services.evaluation_service import EvaluationService
from services.model_registry import model_registry

def test_system():
    """Test the new system"""
    
    print("="*80)
    print("TESTING NEW DOMAIN-BASED ARCHITECTURE")
    print("="*80)
    
    # Initialize services
    print("\n1. Initializing services...")
    model_registry.load_all_models()
    
    # Pass embedder from registry
    embedder = model_registry.get_bi_encoder()
    domain_manager = DomainManager("data", embedder=embedder)
    evaluation_service = EvaluationService("data")
    
    # Test data
    user_id = "default_user"
    domain_name = "JAVA_PROGRAMMING"
    test_question = "explain why multiple inheritance is not applicable in java?"
    
    # Check domain exists
    print(f"\n2. Checking domain: {user_id}/{domain_name}")
    syllabus = domain_manager.load_syllabus(user_id, domain_name)
    
    if not syllabus:
        print("   ✗ Domain not found. Run migrate.py first!")
        return
    
    print(f"   ✓ Course: {syllabus['course_name']}")
    print(f"   ✓ Units: {len(syllabus['units'])}")
    print(f"   ✓ COs: {list(syllabus['course_outcomes'].keys())}")
    
    # Check index
    print(f"\n3. Checking FAISS index...")
    index, metadata = domain_manager.load_index(user_id, domain_name)
    
    if not index:
        print("   ✗ Index not found!")
        return
    
    print(f"   ✓ Index loaded: {index.ntotal} vectors")
    print(f"   ✓ Metadata: {len(metadata)} chunks")
    
    # Test Bloom prediction
    print(f"\n4. Testing Bloom classifier...")
    bloom_result = model_registry.predict_bloom(test_question)
    print(f"   ✓ Bloom Level: {bloom_result['bloom_level']}")
    print(f"   ✓ Confidence: {bloom_result['confidence']:.3f}")
    
    # Test full evaluation
    print(f"\n5. Testing full evaluation pipeline...")
    print(f"   Question: {test_question}")
    
    result = evaluation_service.evaluate_question(user_id, domain_name, test_question)
    
    print(f"\n   RESULTS:")
    print(f"   ✓ Bloom Level: {result['bloom_level']}")
    print(f"   ✓ Unit: {result.get('unit', 'N/A')} - {result.get('unit_title', 'N/A')}")
    print(f"   ✓ Topic: {result.get('topic', 'N/A')}")
    print(f"   ✓ Course Outcomes: {result.get('course_outcomes', [])}")
    
    if result.get('course_outcomes'):
        for co in result['course_outcomes']:
            print(f"      {co}: {syllabus['course_outcomes'][co]}")
    
    print(f"\n   Relevant Subtopics:")
    for st in result.get('subtopics', [])[:3]:
        print(f"      - {st}")
    
    print(f"\n   Top Relevant Chunks:")
    for i, chunk in enumerate(result.get('relevant_chunks', [])[:2], 1):
        print(f"      {i}. {chunk['book'][:50]}... (Page {chunk['page']})")
        print(f"         {chunk['text'][:100]}...")
    
    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED!")
    print("="*80)

if __name__ == "__main__":
    test_system()
