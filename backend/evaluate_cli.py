#!/usr/bin/env python3
"""
CLI Evaluation Tool for Question Intelligence System
Run comprehensive evaluation and display metrics in terminal
"""

import os
import sys
import time
import argparse
from colorama import Colorama, Fore, Style, init

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from agent.orchestrator import AgentOrchestrator
from tools.system_evaluator import SystemEvaluator

# Initialize colorama for colored output
init(autoreset=True)

def print_header(title):
    """Print formatted header"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{title.center(60)}")
    print(f"{Fore.CYAN}{'='*60}")

def print_section(title):
    """Print section header"""
    print(f"\n{Fore.YELLOW}{title}")
    print(f"{Fore.YELLOW}{'-'*len(title)}")

def print_metric(name, value, unit="", color=Fore.GREEN):
    """Print formatted metric"""
    print(f"{color}{name:<25}: {value}{unit}")

def print_confusion_matrix(cm):
    """Print formatted confusion matrix"""
    print(f"\n{Fore.MAGENTA}Confusion Matrix:")
    print(f"{Fore.WHITE}                 Predicted")
    print(f"{Fore.WHITE}                IN    OUT")
    print(f"{Fore.WHITE}Actual    IN   {cm['true_positives']:3d}   {cm['false_negatives']:3d}")
    print(f"{Fore.WHITE}          OUT  {cm['false_positives']:3d}   {cm['true_negatives']:3d}")

def print_category_performance(categories):
    """Print category-wise performance"""
    print(f"\n{Fore.MAGENTA}Category Performance:")
    for category, stats in categories.items():
        accuracy_color = Fore.GREEN if stats['accuracy'] >= 0.8 else Fore.YELLOW if stats['accuracy'] >= 0.6 else Fore.RED
        print(f"{accuracy_color}{category:<15}: {stats['accuracy']:.3f} ({stats['count']} tests)")

def print_detailed_results(results, show_all=False):
    """Print detailed test results"""
    print_section("Detailed Test Results")
    
    correct_count = 0
    for i, result in enumerate(results, 1):
        if "error" in result:
            print(f"{Fore.RED}{i:2d}. ERROR: {result['question'][:50]}... - {result['error']}")
            continue
            
        # Determine result color
        if result['scope_correct'] and result['co_correct']:
            color = Fore.GREEN
            status = "✓ PASS"
            correct_count += 1
        else:
            color = Fore.RED
            status = "✗ FAIL"
        
        # Show result
        if show_all or not (result['scope_correct'] and result['co_correct']):
            print(f"{color}{i:2d}. {status} - {result['question'][:45]}...")
            print(f"    Expected: {result['expected_scope']} | Predicted: {result['predicted_scope']} | Score: {result.get('similarity_score', 'N/A')}")
            if result['expected_scope'] == 'IN':
                print(f"    CO Expected: {result['expected_co']} | Predicted: {result.get('predicted_co', 'N/A')}")
    
    print(f"\n{Fore.CYAN}Summary: {correct_count}/{len(results)} tests passed")

def run_evaluation(course_name, show_details=False, show_all=False):
    """Run comprehensive evaluation"""
    
    print_header("Question Intelligence System - Evaluation")
    print(f"{Fore.WHITE}Course: {course_name}")
    print(f"{Fore.WHITE}Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize system
    print(f"\n{Fore.YELLOW}Initializing system...")
    storage_path = os.path.join(os.path.dirname(__file__), "storage")
    orchestrator = AgentOrchestrator(storage_path)
    
    try:
        orchestrator.load_models()
        print(f"{Fore.GREEN}✓ Models loaded successfully")
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to load models: {e}")
        return
    
    # Run evaluation
    print(f"\n{Fore.YELLOW}Running evaluation tests...")
    evaluator = SystemEvaluator(orchestrator)
    
    start_time = time.time()
    try:
        results = evaluator.run_comprehensive_evaluation(course_name)
    except Exception as e:
        print(f"{Fore.RED}✗ Evaluation failed: {e}")
        return
    
    evaluation_time = time.time() - start_time
    
    # Display results
    metrics = results['metrics']
    
    print_section("Overall Performance Metrics")
    print_metric("Overall Accuracy", f"{metrics['overall_accuracy']:.3f}", "", 
                 Fore.GREEN if metrics['overall_accuracy'] >= 0.8 else Fore.YELLOW if metrics['overall_accuracy'] >= 0.6 else Fore.RED)
    print_metric("Scope Accuracy", f"{metrics['scope_accuracy']:.3f}")
    print_metric("CO Accuracy", f"{metrics['co_accuracy']:.3f}")
    print_metric("Evaluation Time", f"{evaluation_time:.2f}", " seconds")
    print_metric("Avg Response Time", f"{metrics['avg_response_time']:.3f}", " seconds")
    
    print_section("Classification Metrics")
    print_metric("Precision", f"{metrics['precision']:.3f}")
    print_metric("Recall", f"{metrics['recall']:.3f}")
    print_metric("F1-Score", f"{metrics['f1_score']:.3f}")
    
    print_confusion_matrix(metrics['confusion_matrix'])
    
    print_section("Similarity Analysis")
    sim_stats = metrics['similarity_stats']
    print_metric("Avg Similarity", f"{sim_stats['avg_similarity']:.3f}")
    print_metric("In-Syllabus Avg", f"{sim_stats['avg_in_syllabus']:.3f}")
    print_metric("Out-Syllabus Avg", f"{sim_stats['avg_out_syllabus']:.3f}")
    print_metric("Separation", f"{sim_stats['separation']:.3f}", "", 
                 Fore.GREEN if sim_stats['separation'] >= 0.3 else Fore.YELLOW if sim_stats['separation'] >= 0.1 else Fore.RED)
    
    print_category_performance(metrics['category_performance'])
    
    # Show detailed results if requested
    if show_details:
        print_detailed_results(results['detailed_results'], show_all)
    
    # Summary assessment
    print_section("System Assessment")
    
    overall_score = metrics['overall_accuracy']
    if overall_score >= 0.9:
        assessment = f"{Fore.GREEN}EXCELLENT - Production ready"
    elif overall_score >= 0.8:
        assessment = f"{Fore.GREEN}GOOD - Suitable for deployment"
    elif overall_score >= 0.7:
        assessment = f"{Fore.YELLOW}FAIR - Needs improvement"
    elif overall_score >= 0.6:
        assessment = f"{Fore.YELLOW}POOR - Significant issues"
    else:
        assessment = f"{Fore.RED}CRITICAL - Major problems"
    
    print(f"System Performance: {assessment}")
    
    # Recommendations
    if metrics['precision'] < 0.8:
        print(f"{Fore.YELLOW}⚠ Low precision - too many false positives")
    if metrics['recall'] < 0.8:
        print(f"{Fore.YELLOW}⚠ Low recall - missing valid questions")
    if sim_stats['separation'] < 0.2:
        print(f"{Fore.YELLOW}⚠ Poor similarity separation - adjust thresholds")
    
    print(f"\n{Fore.CYAN}Evaluation completed successfully!")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Question Intelligence System Evaluation")
    parser.add_argument("course_name", help="Name of the course to evaluate")
    parser.add_argument("-d", "--details", action="store_true", help="Show detailed test results")
    parser.add_argument("-a", "--all", action="store_true", help="Show all test results (including passed)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    
    args = parser.parse_args()
    
    if args.no_color:
        # Disable colorama
        Fore.RED = Fore.GREEN = Fore.YELLOW = Fore.BLUE = Fore.MAGENTA = Fore.CYAN = Fore.WHITE = ""
        Style.RESET_ALL = ""
    
    try:
        run_evaluation(args.course_name, args.details, args.all)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Evaluation interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()