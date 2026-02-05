#!/usr/bin/env python3
"""
Simple CLI Evaluation Tool for Question Intelligence System
No external dependencies - basic terminal output
"""

import os
import sys
import time
import argparse

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from agent.orchestrator import AgentOrchestrator
from tools.system_evaluator import SystemEvaluator

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}")

def print_section(title):
    """Print section header"""
    print(f"\n{title}")
    print(f"{'-'*len(title)}")

def print_metric(name, value, unit=""):
    """Print formatted metric"""
    print(f"{name:<25}: {value}{unit}")

def print_confusion_matrix(cm):
    """Print formatted confusion matrix"""
    print(f"\nConfusion Matrix:")
    print(f"                 Predicted")
    print(f"                IN    OUT")
    print(f"Actual    IN   {cm['true_positives']:3d}   {cm['false_negatives']:3d}")
    print(f"          OUT  {cm['false_positives']:3d}   {cm['true_negatives']:3d}")

def print_category_performance(categories):
    """Print category-wise performance"""
    print(f"\nCategory Performance:")
    for category, stats in categories.items():
        status = "GOOD" if stats['accuracy'] >= 0.8 else "FAIR" if stats['accuracy'] >= 0.6 else "POOR"
        print(f"{category:<20}: {stats['accuracy']:.3f} ({stats['total']} tests) [{status}]")



def run_evaluation(course_name, show_details=False, show_all=False):
    """Run comprehensive evaluation"""
    
    print_header("Question Intelligence System - Evaluation")
    print(f"Course: {course_name}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize system
    print(f"\nInitializing system...")
    storage_path = os.path.join(os.path.dirname(__file__), "storage")
    orchestrator = AgentOrchestrator(storage_path)
    
    try:
        orchestrator.load_models()
        print(f"[OK] Models loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load models: {e}")
        return
    
    # Run evaluation
    print(f"\nRunning evaluation tests...")
    evaluator = SystemEvaluator(orchestrator)
    
    start_time = time.time()
    try:
        results = evaluator.evaluate_system(course_name)
    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}")
        return
    
    evaluation_time = time.time() - start_time
    
    # Display results
    metrics = results['metrics']
    
    print_section("Overall Performance Metrics")
    overall_status = "EXCELLENT" if metrics['accuracy'] >= 0.9 else "GOOD" if metrics['accuracy'] >= 0.8 else "FAIR" if metrics['accuracy'] >= 0.7 else "POOR"
    print_metric("Overall Accuracy", f"{metrics['accuracy']:.3f} [{overall_status}]")
    print_metric("Precision", f"{metrics['precision']:.3f}")
    print_metric("Recall", f"{metrics['recall']:.3f}")
    print_metric("F1-Score", f"{metrics['f1_score']:.3f}")
    print_metric("Evaluation Time", f"{evaluation_time:.2f} seconds")
    
    # Confusion Matrix
    cm = metrics['confusion_matrix']
    print(f"\nConfusion Matrix:")
    print(f"                 Predicted")
    print(f"                IN    OUT")
    print(f"Actual    IN   {cm['true_positive']:3d}   {cm['false_negative']:3d}")
    print(f"          OUT  {cm['false_positive']:3d}   {cm['true_negative']:3d}")
    
    # Similarity Analysis
    sim_stats = metrics['similarity_analysis']
    print_section("Similarity Analysis")
    print_metric("In-Syllabus Avg", f"{sim_stats['in_syllabus_avg']:.3f}")
    print_metric("Out-Syllabus Avg", f"{sim_stats['out_syllabus_avg']:.3f}")
    print_metric("In-Syllabus Std", f"{sim_stats['in_syllabus_std']:.3f}")
    print_metric("Out-Syllabus Std", f"{sim_stats['out_syllabus_std']:.3f}")
    
    separation = sim_stats['in_syllabus_avg'] - sim_stats['out_syllabus_avg']
    separation_status = "GOOD" if separation >= 0.3 else "FAIR" if separation >= 0.1 else "POOR"
    print_metric("Separation", f"{separation:.3f} [{separation_status}]")
    
    # Show detailed results if requested
    if show_details:
        print_section("Detailed Test Results")
        for i, result in enumerate(results['results'], 1):
            status = "PASS" if result['correct'] else "FAIL"
            print(f"{i:2d}. {status} - {result['question'][:45]}...")
            print(f"    Expected: {'IN' if result['expected'] else 'OUT'} | Predicted: {'IN' if result['predicted'] else 'OUT'} | Score: {result['similarity_score']:.3f}")
            if not result['correct']:
                print(f"    Category: {result['category']}")
    
    # Summary assessment
    print_section("System Assessment")
    assessment = results['summary']['performance_assessment']
    print(f"System Performance: {assessment}")
    
    # Recommendations
    print("\nRecommendations:")
    for rec in results['summary']['recommendations']:
        print(f"- {rec}")
    
    # Key insights
    print("\nKey Insights:")
    for insight in results['summary']['key_insights']:
        print(f"- {insight}")
    
    print(f"\nEvaluation completed successfully!")
    print(f"Total tests: {results['total_tests']}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Question Intelligence System Evaluation")
    parser.add_argument("course_name", help="Name of the course to evaluate")
    parser.add_argument("-d", "--details", action="store_true", help="Show detailed test results")
    parser.add_argument("-a", "--all", action="store_true", help="Show all test results (including passed)")
    
    args = parser.parse_args()
    
    try:
        run_evaluation(args.course_name, args.details, args.all)
    except KeyboardInterrupt:
        print(f"\nEvaluation interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()