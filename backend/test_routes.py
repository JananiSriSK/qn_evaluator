from fastapi import APIRouter
from models.schemas import EvaluateQuestionRequest, EvaluateQuestionResponse
from agent.orchestrator import AgentOrchestrator
import logging
import os

logger = logging.getLogger(__name__)

# Initialize test router
test_router = APIRouter(prefix="/test", tags=["testing"])

# Initialize orchestrator for testing
STORAGE_PATH = os.path.join(os.path.dirname(__file__), "..", "storage")
test_orchestrator = AgentOrchestrator(STORAGE_PATH)

@test_router.post("/validate-domain-gate")
async def test_domain_gate_validation(course_name: str):
    """Test domain gate with negative samples to verify false positive prevention"""
    try:
        # Load course domain embedding
        test_orchestrator.faiss_storage.load_index(course_name)
        domain_embedding = test_orchestrator.faiss_storage.get_course_domain_embedding(course_name)
        
        if domain_embedding is None:
            return {"error": f"No domain embedding found for course: {course_name}"}
        
        # Run validation tests
        negative_test = test_orchestrator.validation_tester.test_cross_domain_rejection(course_name, domain_embedding)
        positive_test = test_orchestrator.validation_tester.test_positive_samples(course_name, domain_embedding)
        
        return {
            "course_name": course_name,
            "negative_test": negative_test,
            "positive_test": positive_test,
            "overall_validation": {
                "negative_passed": negative_test["validation_passed"],
                "positive_passed": positive_test["validation_passed"],
                "both_passed": negative_test["validation_passed"] and positive_test["validation_passed"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error during domain gate validation: {e}")
        return {"error": str(e)}

@test_router.post("/test-question-batch")
async def test_question_batch():
    """Test a batch of questions to verify validation logic"""
    
    test_questions = [
        # Should be REJECTED (cross-domain)
        {"question": "explain pasta making", "expected": "rejected"},
        {"question": "how to bake a cake", "expected": "rejected"},
        {"question": "what is photosynthesis", "expected": "rejected"},
        
        # Should be ACCEPTED (OS-related)
        {"question": "explain process synchronization", "expected": "accepted"},
        {"question": "what is deadlock detection", "expected": "accepted"},
        {"question": "describe CPU scheduling", "expected": "accepted"}
    ]
    
    course_name = "INTRODUCTION TO OPERATING SYSTEM"
    results = []
    
    for test_case in test_questions:
        try:
            # Evaluate question
            result = test_orchestrator.evaluate_question(course_name, test_case["question"])
            
            # Check if result matches expectation
            is_rejected = result.get("out_of_syllabus", False)
            expected_rejection = test_case["expected"] == "rejected"
            
            correct_prediction = is_rejected == expected_rejection
            
            results.append({
                "question": test_case["question"],
                "expected": test_case["expected"],
                "actual": "rejected" if is_rejected else "accepted",
                "correct": correct_prediction,
                "similarity_score": result.get("similarity_score"),
                "domain_similarity": result.get("domain_similarity"),
                "reason": result.get("reason")
            })
            
        except Exception as e:
            results.append({
                "question": test_case["question"],
                "error": str(e)
            })
    
    # Calculate accuracy
    correct_predictions = sum(1 for r in results if r.get("correct", False))
    total_tests = len(test_questions)
    accuracy = correct_predictions / total_tests if total_tests > 0 else 0
    
    return {
        "total_tests": total_tests,
        "correct_predictions": correct_predictions,
        "accuracy": round(accuracy, 3),
        "results": results,
        "validation_passed": accuracy >= 0.8  # 80% accuracy required
    }