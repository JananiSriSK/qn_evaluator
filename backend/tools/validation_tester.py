import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ValidationTester:
    """Test validation logic with negative samples to prevent false positives"""
    
    def __init__(self, embedding_tool):
        self.embedding_tool = embedding_tool
    
    def test_cross_domain_rejection(self, course_name: str, domain_embedding: np.ndarray) -> Dict[str, Any]:
        """Test that obviously wrong questions are rejected"""
        
        # Negative test cases (should be rejected)
        negative_questions = [
            "explain pasta making",
            "how to bake a cake", 
            "what is photosynthesis",
            "solve quadratic equations",
            "french grammar rules",
            "stock market analysis",
            "painting techniques",
            "football strategies"
        ]
        
        results = {}
        DOMAIN_THRESHOLD = 0.75
        
        for question in negative_questions:
            # Generate question embedding
            question_embedding = self.embedding_tool.generate_embeddings([question])[0]
            
            # Compute domain similarity
            domain_similarity = np.dot(question_embedding, domain_embedding)
            
            # Check if correctly rejected
            is_rejected = domain_similarity < DOMAIN_THRESHOLD
            
            results[question] = {
                "domain_similarity": round(domain_similarity, 3),
                "correctly_rejected": is_rejected,
                "threshold": DOMAIN_THRESHOLD
            }
            
            logger.info(f"Test: '{question}' -> similarity: {domain_similarity:.3f}, rejected: {is_rejected}")
        
        # Calculate rejection rate
        total_tests = len(negative_questions)
        correct_rejections = sum(1 for r in results.values() if r["correctly_rejected"])
        rejection_rate = correct_rejections / total_tests
        
        return {
            "course_name": course_name,
            "total_negative_tests": total_tests,
            "correct_rejections": correct_rejections,
            "rejection_rate": round(rejection_rate, 3),
            "results": results,
            "validation_passed": rejection_rate >= 0.8  # 80% rejection rate required
        }
    
    def test_positive_samples(self, course_name: str, domain_embedding: np.ndarray) -> Dict[str, Any]:
        """Test that relevant questions are accepted"""
        
        # Positive test cases for OS course (should be accepted)
        positive_questions = [
            "explain process synchronization",
            "what is deadlock detection",
            "describe CPU scheduling algorithms", 
            "how does memory management work",
            "explain file system operations",
            "what are system calls",
            "describe thread management"
        ]
        
        results = {}
        DOMAIN_THRESHOLD = 0.75
        
        for question in positive_questions:
            # Generate question embedding
            question_embedding = self.embedding_tool.generate_embeddings([question])[0]
            
            # Compute domain similarity
            domain_similarity = np.dot(question_embedding, domain_embedding)
            
            # Check if correctly accepted
            is_accepted = domain_similarity >= DOMAIN_THRESHOLD
            
            results[question] = {
                "domain_similarity": round(domain_similarity, 3),
                "correctly_accepted": is_accepted,
                "threshold": DOMAIN_THRESHOLD
            }
            
            logger.info(f"Test: '{question}' -> similarity: {domain_similarity:.3f}, accepted: {is_accepted}")
        
        # Calculate acceptance rate
        total_tests = len(positive_questions)
        correct_acceptances = sum(1 for r in results.values() if r["correctly_accepted"])
        acceptance_rate = correct_acceptances / total_tests
        
    def test_contrastive_domain_gate(self, course_name: str, domain_embedding: np.ndarray, boundary_embedding: np.ndarray = None) -> Dict[str, Any]:
        """Test contrastive domain gate with generic procedural questions"""
        
        if boundary_embedding is None:
            logger.warning("No boundary embedding available - skipping contrastive test")
            return {"validation_passed": True, "reason": "No boundary embedding to test"}
        
        # Generic procedural questions (should be rejected)
        generic_questions = [
            "explain the process",
            "what is the method", 
            "describe the procedure",
            "how to implement",
            "what are the steps",
            "define the concept"
        ]
        
        results = {}
        CONTRASTIVE_THRESHOLD = 0.15
        
        for question in generic_questions:
            question_embedding = self.embedding_tool.generate_embeddings([question])[0]
            
            domain_sim = np.dot(question_embedding, domain_embedding)
            boundary_sim = np.dot(question_embedding, boundary_embedding)
            contrastive_score = domain_sim - boundary_sim
            
            is_rejected = contrastive_score < CONTRASTIVE_THRESHOLD
            
            results[question] = {
                "domain_similarity": round(domain_sim, 3),
                "boundary_similarity": round(boundary_sim, 3), 
                "contrastive_score": round(contrastive_score, 3),
                "correctly_rejected": is_rejected,
                "threshold": CONTRASTIVE_THRESHOLD
            }
            
            logger.info(f"Contrastive test: '{question}' -> score: {contrastive_score:.3f}, rejected: {is_rejected}")
        
        correct_rejections = sum(1 for r in results.values() if r["correctly_rejected"])
        rejection_rate = correct_rejections / len(generic_questions)
        
        return {
            "course_name": course_name,
            "total_tests": len(generic_questions),
            "correct_rejections": correct_rejections,
            "rejection_rate": round(rejection_rate, 3),
            "results": results,
            "validation_passed": rejection_rate >= 0.7  # 70% rejection rate required
        }