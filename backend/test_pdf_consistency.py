"""Test PDF vs Single mode consistency"""
from services.model_registry import model_registry
from services.evaluation_service import EvaluationService
from services.pdf_parser import PDFQuestionParser
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

# Load models
model_registry.load_all_models()
eval_service = EvaluationService('data')

# Test questions
test_cases = [
    "Define process and list different states of a process.",
    "Define paging and segmentation.",
    "Explain Gantt chart scheduling.",
]

print("=" * 100)
print("CONSISTENCY TEST: PDF Parser vs Direct Evaluation")
print("=" * 100)

for test_q in test_cases:
    print(f"\n{'='*100}")
    print(f"TEST: {test_q}")
    print(f"{'='*100}")
    
    # Simulate PDF extraction (with numbering)
    pdf_text = f"3. {test_q}"
    
    # PDF mode: Parser cleans, then EvaluationService cleans
    print("\n[PDF MODE]")
    pdf_cleaned = PDFQuestionParser.clean_question(pdf_text)
    print(f"After PDF parser: '{pdf_cleaned}'")
    result_pdf = eval_service.evaluate_question('1', 'OPERATING SYSTEM', pdf_cleaned)
    
    # Single mode: Only EvaluationService cleans
    print("\n[SINGLE MODE]")
    result_single = eval_service.evaluate_question('1', 'OPERATING SYSTEM', test_q)
    
    # Compare
    print(f"\n[RESULTS]")
    print(f"PDF:    Topic='{result_pdf.get('topic')}', Unit={result_pdf.get('unit')}, OOS={result_pdf.get('out_of_syllabus')}")
    print(f"Single: Topic='{result_single.get('topic')}', Unit={result_single.get('unit')}, OOS={result_single.get('out_of_syllabus')}")
    
    if result_pdf.get('topic') == result_single.get('topic'):
        print("✓ MATCH")
    else:
        print("✗ MISMATCH")
