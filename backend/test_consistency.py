"""Test consistency between single and batch evaluation"""
from services.model_registry import model_registry
from services.evaluation_service import EvaluationService
import logging

logging.basicConfig(level=logging.INFO)

# Load models
model_registry.load_all_models()

# Initialize service
eval_service = EvaluationService('data')

# Test question
test_question = "Define paging and segmentation."

# Simulate PDF extraction (with numbering)
pdf_extracted = "3. Define paging and segmentation."

print("=" * 80)
print("CONSISTENCY TEST: Single vs Batch Evaluation")
print("=" * 80)

# Test 1: Clean single question
print("\n[TEST 1] Single question evaluation:")
result1 = eval_service.evaluate_question('1', 'OPERATING SYSTEM', test_question)
print(f"Topic: {result1.get('topic')}")
print(f"Unit: {result1.get('unit')}")
print(f"Out of Syllabus: {result1.get('out_of_syllabus')}")

# Test 2: Simulate PDF batch (with numbering)
print("\n[TEST 2] PDF batch evaluation (with numbering):")
result2 = eval_service.evaluate_question('1', 'OPERATING SYSTEM', pdf_extracted)
print(f"Topic: {result2.get('topic')}")
print(f"Unit: {result2.get('unit')}")
print(f"Out of Syllabus: {result2.get('out_of_syllabus')}")

# Test 3: Verify cleaning
print("\n[TEST 3] Text cleaning verification:")
cleaned1 = EvaluationService.clean_question_text(test_question)
cleaned2 = EvaluationService.clean_question_text(pdf_extracted)
print(f"Original: '{test_question}'")
print(f"Cleaned:  '{cleaned1}'")
print(f"PDF extracted: '{pdf_extracted}'")
print(f"Cleaned:       '{cleaned2}'")
print(f"Match: {cleaned1 == cleaned2}")

print("\n" + "=" * 80)
if result1.get('topic') == result2.get('topic') and result1.get('unit') == result2.get('unit'):
    print("✓ CONSISTENCY TEST PASSED")
else:
    print("✗ CONSISTENCY TEST FAILED")
print("=" * 80)
