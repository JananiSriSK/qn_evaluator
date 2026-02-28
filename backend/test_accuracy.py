"""
Test improved topic selection accuracy
Run after enriching syllabus
"""

from services.evaluation_service import EvaluationService
from services.model_registry import model_registry

# Load models
print("Loading models...")
model_registry.load_all_models()

# Initialize service
eval_service = EvaluationService("data")

# Test questions
test_questions = [
    "List the features of Java programming language",
    "What is a Servlet and explain its lifecycle?",
    "Explain Hibernate framework and its advantages",
    "What are the types of inheritance in Java?",
    "Describe socket programming in Java"
]

print("\n" + "="*70)
print("ACCURACY TEST - Improved Topic Selection")
print("="*70)

for i, question in enumerate(test_questions, 1):
    print(f"\n{i}. Question: {question}")
    print("-" * 70)
    
    try:
        result = eval_service.evaluate_question("1", "JAVA_PROGRAMMING", question)
        
        print(f"   Unit: {result.get('unit', 'N/A')}")
        print(f"   Topic: {result.get('topic', 'N/A')}")
        print(f"   COs: {', '.join(result.get('course_outcomes', []))}")
        print(f"   Bloom: {result['bloom_level']} ({result['bloom_confidence']:.2f})")
        
        if result.get('warning'):
            print(f"   Warning: {result['warning']}")
    
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "="*70)
print("Expected Mappings:")
print("="*70)
print("1. Features of Java → Unit I, Overview of Java, CO1")
print("2. Servlet lifecycle → Unit IV, Servlet lifecycle, CO4")
print("3. Hibernate → Unit V, Hibernate, CO5")
print("4. Inheritance types → Unit I, Inheritance, CO1")
print("5. Socket programming → Unit II, Using stream sockets, CO2")
