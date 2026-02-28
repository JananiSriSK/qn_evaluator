"""
API Testing Script for Question Intelligence System v2.0
Tests all REST endpoints for frontend integration
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8002"

def test_health():
    """Test health check"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_domain():
    """Test domain creation"""
    print("\n=== Testing Domain Creation ===")
    data = {
        "user_id": "test_user",
        "domain_name": "TEST_DOMAIN"
    }
    response = requests.post(f"{BASE_URL}/domains/create", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_list_domains():
    """Test listing domains"""
    print("\n=== Testing List Domains ===")
    response = requests.get(f"{BASE_URL}/domains/test_user")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_upload_syllabus():
    """Test syllabus upload"""
    print("\n=== Testing Syllabus Upload ===")
    
    # Check if syllabus exists
    syllabus_path = Path("extract/syllabus.txt")
    if not syllabus_path.exists():
        print("❌ Syllabus file not found at extract/syllabus.txt")
        return False
    
    with open(syllabus_path, "rb") as f:
        files = {"file": ("syllabus.txt", f, "text/plain")}
        response = requests.post(
            f"{BASE_URL}/domains/test_user/TEST_DOMAIN/syllabus",
            files=files
        )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_upload_books():
    """Test books upload"""
    print("\n=== Testing Books Upload ===")
    
    # Check if books exist
    books_path = Path("extract/books")
    if not books_path.exists():
        print("❌ Books directory not found at extract/books")
        return False
    
    pdf_files = list(books_path.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in extract/books")
        return False
    
    files = []
    for pdf in pdf_files[:2]:  # Upload first 2 books for testing
        files.append(("files", (pdf.name, open(pdf, "rb"), "application/pdf")))
    
    response = requests.post(
        f"{BASE_URL}/domains/test_user/TEST_DOMAIN/books",
        files=files
    )
    
    # Close files
    for _, (_, f, _) in files:
        f.close()
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_domain_status():
    """Test domain status"""
    print("\n=== Testing Domain Status ===")
    response = requests.get(f"{BASE_URL}/domains/test_user/TEST_DOMAIN/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_evaluate_question():
    """Test single question evaluation"""
    print("\n=== Testing Question Evaluation ===")
    data = {
        "user_id": "test_user",
        "domain_name": "TEST_DOMAIN",
        "question": "Explain why multiple inheritance is not applicable in Java?"
    }
    response = requests.post(f"{BASE_URL}/evaluate", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        print(f"Question: {result['question']}")
        print(f"Unit: {result['unit']}")
        print(f"Topic: {result['topic']}")
        print(f"Bloom Level: {result['bloom_level']} (confidence: {result['bloom_confidence']:.2f})")
        print(f"Course Outcomes: {result['course_outcomes']}")
        print(f"Subtopics: {len(result.get('subtopics', []))}")
        print(f"Relevant Chunks: {len(result.get('relevant_chunks', []))}")
    else:
        print(f"Error: {result}")
    
    return response.status_code == 200

def test_delete_domain():
    """Test domain deletion"""
    print("\n=== Testing Domain Deletion ===")
    response = requests.delete(f"{BASE_URL}/domains/test_user/TEST_DOMAIN")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_existing_domain():
    """Test with existing default_user/JAVA_PROGRAMMING domain"""
    print("\n=== Testing Existing Domain ===")
    
    # Check status
    response = requests.get(f"{BASE_URL}/domains/default_user/JAVA_PROGRAMMING/status")
    print(f"Status Check: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("❌ Default domain not found")
        return False
    
    # Evaluate question
    data = {
        "user_id": "default_user",
        "domain_name": "JAVA_PROGRAMMING",
        "question": "What is polymorphism in Java?"
    }
    response = requests.post(f"{BASE_URL}/evaluate", json=data)
    print(f"\nEvaluation Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Unit: {result['unit']}")
        print(f"Topic: {result['topic']}")
        print(f"Bloom: {result['bloom_level']} ({result['bloom_confidence']:.2f})")
    else:
        print(f"Error: {response.json()}")
    
    return response.status_code == 200

def run_full_test():
    """Run complete test suite"""
    print("=" * 60)
    print("Question Intelligence System v2.0 - API Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Create Domain", test_create_domain),
        ("List Domains", test_list_domains),
        ("Upload Syllabus", test_upload_syllabus),
        ("Upload Books", test_upload_books),
        ("Domain Status", test_domain_status),
        ("Evaluate Question", test_evaluate_question),
        ("Delete Domain", test_delete_domain),
        ("Test Existing Domain", test_existing_domain)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "✓ PASS" if success else "✗ FAIL"))
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append((name, f"✗ ERROR: {str(e)[:50]}"))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for name, result in results:
        print(f"{name:.<40} {result}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    print(f"\nTotal: {passed}/{len(tests)} passed")

if __name__ == "__main__":
    run_full_test()
