"""
System Evaluator Tool for Question Intelligence System
Provides comprehensive evaluation metrics and test cases
"""

import logging
from typing import Dict, List, Tuple, Any
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

logger = logging.getLogger(__name__)

class SystemEvaluator:
    """Comprehensive evaluation tool for the Question Intelligence System"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        
        # Predefined test cases for evaluation
        self.test_cases = {
            "INTRODUCTION TO OPERATING SYSTEM": [
                # IN-SYLLABUS QUESTIONS 
                ("What is the difference between process and thread?", True, "Core OS concept"),
                ("Explain the concept of virtual memory management", True, "Memory management"),
                ("What are the different CPU scheduling algorithms?", True, "Process scheduling"),
                ("Describe the producer-consumer problem", True, "Process synchronization"),
                ("What is deadlock and how can it be prevented?", True, "Deadlock handling"),
                ("Explain the concept of file allocation methods", True, "File systems"),
                ("What are the different types of operating systems?", True, "OS types"),
                ("Describe the concept of paging in memory management", True, "Memory management"),
                ("What is the role of device drivers in an operating system?", True, "I/O management"),
                ("Explain the concept of semaphores in process synchronization", True, "Synchronization"),
                
                # OUT-OF-SYLLABUS QUESTIONS 
                ("How do you make chocolate chip cookies?", False, "Cooking"),
                ("What is photosynthesis in plants?", False, "Biology"),
                ("Solve the quadratic equation x² + 5x + 6 = 0", False, "Mathematics"),
                ("What are the principles of machine learning?", False, "AI/ML"),
                ("How does DNA replication work?", False, "Biology"),
                ("What is the capital of France?", False, "Geography"),
                ("Explain the theory of relativity", False, "Physics"),
                ("How to invest in stock market?", False, "Finance"),
                ("What are the benefits of yoga?", False, "Health"),
                ("How to write a resume?", False, "Career"),
                
                # BORDERLINE QUESTIONS (Could go either way)
                ("What is computer architecture?", False, "Related but different domain"),
                ("Explain network protocols", False, "Networking - different course"),
                ("What is database normalization?", False, "Database - different course"),
                ("How does compiler work?", False, "Compiler design - different course"),
                ("What is software engineering lifecycle?", False, "Software engineering - different course")
            ]
        }
    
    def evaluate_system(self, course_name: str) -> Dict[str, Any]:
        """Run comprehensive evaluation on the system"""
        if course_name not in self.test_cases:
            raise ValueError(f"No test cases available for course: {course_name}")
        
        test_cases = self.test_cases[course_name]
        results = []
        predictions = []
        ground_truth = []
        similarity_scores = []
        
        logger.info(f"Starting evaluation with {len(test_cases)} test cases")
        
        for i, (question, expected, category) in enumerate(test_cases):
            try:
                # Evaluate question
                result = self.orchestrator.evaluate_question(course_name, question)
                
                # Extract prediction and similarity
                predicted = not result.get("out_of_syllabus", False)
                similarity = result.get("similarity_score", 0.0)
                
                predictions.append(predicted)
                ground_truth.append(expected)
                similarity_scores.append(similarity)
                
                results.append({
                    "question": question,
                    "expected": expected,
                    "predicted": predicted,
                    "correct": predicted == expected,
                    "similarity_score": similarity,
                    "category": category,
                    "result": result
                })
                
                logger.info(f"Test {i+1}/{len(test_cases)}: {'✓' if predicted == expected else '✗'}")
                
            except Exception as e:
                logger.error(f"Error evaluating question {i+1}: {e}")
                # Treat errors as out-of-syllabus predictions
                predictions.append(False)
                ground_truth.append(expected)
                similarity_scores.append(0.0)
                
                results.append({
                    "question": question,
                    "expected": expected,
                    "predicted": False,
                    "correct": False == expected,
                    "similarity_score": 0.0,
                    "category": category,
                    "result": {"error": str(e)}
                })
        
        # Calculate metrics
        metrics = self._calculate_metrics(ground_truth, predictions, similarity_scores)
        
        return {
            "course_name": course_name,
            "total_tests": len(test_cases),
            "results": results,
            "metrics": metrics,
            "summary": self._generate_summary(results, metrics)
        }
    
    def _calculate_metrics(self, ground_truth: List[bool], predictions: List[bool], 
                          similarities: List[float]) -> Dict[str, Any]:
        """Calculate comprehensive evaluation metrics"""
        
        # Basic classification metrics
        accuracy = accuracy_score(ground_truth, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            ground_truth, predictions, average='binary', zero_division=0
        )
        
        # Confusion matrix
        cm = confusion_matrix(ground_truth, predictions)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        # Similarity analysis
        in_syllabus_similarities = [s for i, s in enumerate(similarities) if ground_truth[i]]
        out_syllabus_similarities = [s for i, s in enumerate(similarities) if not ground_truth[i]]
        
        return {
            "accuracy": round(accuracy, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp)
            },
            "similarity_analysis": {
                "in_syllabus_avg": round(np.mean(in_syllabus_similarities), 3) if in_syllabus_similarities else 0,
                "out_syllabus_avg": round(np.mean(out_syllabus_similarities), 3) if out_syllabus_similarities else 0,
                "in_syllabus_std": round(np.std(in_syllabus_similarities), 3) if in_syllabus_similarities else 0,
                "out_syllabus_std": round(np.std(out_syllabus_similarities), 3) if out_syllabus_similarities else 0
            }
        }
    
    def _generate_summary(self, results: List[Dict], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate evaluation summary and recommendations"""
        
        # Category-wise analysis
        categories = {}
        for result in results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "correct": 0}
            categories[cat]["total"] += 1
            if result["correct"]:
                categories[cat]["correct"] += 1
        
        # Calculate category accuracies
        for cat in categories:
            categories[cat]["accuracy"] = round(
                categories[cat]["correct"] / categories[cat]["total"], 3
            )
        
        # Performance assessment
        accuracy = metrics["accuracy"]
        if accuracy >= 0.9:
            assessment = "Excellent"
        elif accuracy >= 0.8:
            assessment = "Good"
        elif accuracy >= 0.7:
            assessment = "Fair"
        else:
            assessment = "Needs Improvement"
        
        # Generate recommendations
        recommendations = []
        if metrics["precision"] < 0.8:
            recommendations.append("Consider tightening domain validation to reduce false positives")
        if metrics["recall"] < 0.8:
            recommendations.append("Consider expanding syllabus coverage or lowering similarity thresholds")
        if metrics["confusion_matrix"]["false_positive"] > 2:
            recommendations.append("High false positive rate - strengthen out-of-domain detection")
        if metrics["confusion_matrix"]["false_negative"] > 2:
            recommendations.append("High false negative rate - review syllabus completeness")
        
        return {
            "performance_assessment": assessment,
            "category_performance": categories,
            "recommendations": recommendations,
            "key_insights": [
                f"Overall accuracy: {accuracy*100:.1f}%",
                f"Precision: {metrics['precision']*100:.1f}%",
                f"Recall: {metrics['recall']*100:.1f}%",
                f"F1-Score: {metrics['f1_score']*100:.1f}%"
            ]
        }