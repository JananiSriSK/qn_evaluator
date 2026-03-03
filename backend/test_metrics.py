"""
Evaluation Metrics Test Script
Tests the Question Intelligence System and displays performance metrics
"""

import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.model_registry import model_registry
from services.evaluation_service import EvaluationService
from services.mongodb_storage import MongoDBStorage

# Test questions with expected outputs
TEST_QUESTIONS = [
    {
        "question": "Define inheritance with an example",
        "expected_bt": "BT1",
        "expected_unit": "I",
        "domain": "JAVA_PROGRAMMING"
    },
    {
        "question": "Explain the difference between abstract class and interface",
        "expected_bt": "BT2",
        "expected_unit": "I",
        "domain": "JAVA_PROGRAMMING"
    },
    {
        "question": "Compare deadlock prevention and deadlock avoidance",
        "expected_bt": "BT4",
        "expected_unit": "III",
        "domain": "OPERATING SYSTEM"
    },
    {
        "question": "What is method overloading?",
        "expected_bt": "BT1",
        "expected_unit": "I",
        "domain": "JAVA_PROGRAMMING"
    },
    {
        "question": "Implement a program to demonstrate multithreading",
        "expected_bt": "BT3",
        "expected_unit": "II",
        "domain": "JAVA_PROGRAMMING"
    }
]

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_metric(label, value, unit=""):
    """Print formatted metric"""
    print(f"  {label:.<50} {value}{unit}")

def test_system():
    """Run comprehensive system tests"""
    
    print_header("QUESTION INTELLIGENCE SYSTEM - EVALUATION METRICS")
    
    # Initialize
    print("\n[1/5] Initializing System...")
    start_time = time.time()
    
    try:
        mongo_storage = MongoDBStorage()
        print("  [OK] MongoDB connected")
    except Exception as e:
        print(f"  [FAIL] MongoDB connection failed: {e}")
        return
    
    model_registry.load_all_models()
    print("  [OK] Models loaded")
    
    evaluation_service = EvaluationService("data", mongo_storage=mongo_storage)
    print("  [OK] Evaluation service ready")
    
    init_time = time.time() - start_time
    print_metric("Initialization time", f"{init_time:.2f}", "s")
    
    # Test evaluations
    print_header("EVALUATION PERFORMANCE METRICS")
    
    results = []
    total_time = 0
    correct_bt = 0
    correct_unit = 0
    in_syllabus = 0
    
    for i, test in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Testing: {test['question'][:50]}...")
        
        start = time.time()
        try:
            result = evaluation_service.evaluate_question(
                "1", 
                test["domain"], 
                test["question"]
            )
            eval_time = time.time() - start
            total_time += eval_time
            
            # Check accuracy
            bt_match = result.get("bloom_level") == test["expected_bt"]
            unit_match = result.get("unit") == test["expected_unit"]
            not_oos = not result.get("out_of_syllabus", False)
            
            if bt_match:
                correct_bt += 1
            if unit_match:
                correct_unit += 1
            if not_oos:
                in_syllabus += 1
            
            results.append({
                "question": test["question"][:40],
                "time": eval_time,
                "bt_predicted": result.get("bloom_level"),
                "bt_expected": test["expected_bt"],
                "bt_correct": "OK" if bt_match else "X",
                "unit_predicted": result.get("unit"),
                "unit_expected": test["expected_unit"],
                "unit_correct": "OK" if unit_match else "X",
                "confidence": result.get("bloom_confidence", 0),
                "oos": result.get("out_of_syllabus", False)
            })
            
            print(f"  Time: {eval_time:.3f}s | BT: {result.get('bloom_level')} {'[OK]' if bt_match else '[X]'} | Unit: {result.get('unit')} {'[OK]' if unit_match else '[X]'}")
            
        except Exception as e:
            print(f"  [X] Error: {e}")
            results.append({
                "question": test["question"][:40],
                "time": 0,
                "error": str(e)
            })
    
    # Summary metrics
    print_header("PERFORMANCE SUMMARY")
    
    avg_time = total_time / len(TEST_QUESTIONS)
    bt_accuracy = (correct_bt / len(TEST_QUESTIONS)) * 100
    unit_accuracy = (correct_unit / len(TEST_QUESTIONS)) * 100
    syllabus_coverage = (in_syllabus / len(TEST_QUESTIONS)) * 100
    
    print_metric("Total questions tested", len(TEST_QUESTIONS))
    print_metric("Average evaluation time", f"{avg_time:.3f}", "s")
    print_metric("Total evaluation time", f"{total_time:.2f}", "s")
    print_metric("Bloom Taxonomy accuracy", f"{bt_accuracy:.1f}", "%")
    print_metric("Unit mapping accuracy", f"{unit_accuracy:.1f}", "%")
    print_metric("In-syllabus detection", f"{syllabus_coverage:.1f}", "%")
    
    # Model info
    print_header("MODEL INFORMATION")
    print_metric("Bi-Encoder", "all-MiniLM-L6-v2 (384 dims)")
    print_metric("Cross-Encoder", "ms-marco-MiniLM-L-6-v2")
    print_metric("Bloom Classifier", "DistilBERT fine-tuned")
    print_metric("Enrichment LLM", "Llama 3.3 70B (Groq)")
    
    # Storage info
    print_header("STORAGE INFORMATION")
    print_metric("Primary storage", "MongoDB (localhost:27017)")
    print_metric("Vector index", "FAISS IndexFlatIP")
    print_metric("Large files", "GridFS")
    
    # Detailed results table
    print_header("DETAILED RESULTS")
    print(f"\n{'Question':<42} {'Time':<8} {'BT':<8} {'Unit':<8} {'Conf':<6}")
    print("-" * 70)
    
    for r in results:
        if "error" not in r:
            bt_pred = r['bt_predicted'] or "N/A"
            unit_pred = r['unit_predicted'] or "N/A"
            print(f"{r['question']:<42} {r['time']:.3f}s   "
                  f"{bt_pred:<3}{r['bt_correct']:<3} "
                  f"{unit_pred:<3}{r['unit_correct']:<3} "
                  f"{r['confidence']:.2f}")
        else:
            print(f"{r['question']:<42} ERROR: {r['error']}")
    
    print("\n" + "="*70)
    print("  Test completed successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_system()
