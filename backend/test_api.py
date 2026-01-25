import requests
import json

# Test data
test_course = {
    "course_name": "Data Structures",
    "syllabus": [
        {
            "unit_number": 1,
            "title": "Arrays and Linked Lists",
            "content": "Introduction to arrays, dynamic arrays, singly linked lists, doubly linked lists, operations on linked lists"
        },
        {
            "unit_number": 2,
            "title": "Stacks and Queues",
            "content": "Stack operations, queue operations, circular queues, priority queues, applications"
        }
    ],
    "course_outcomes": [
        {
            "id": "CO1",
            "description": "Understand fundamental data structures and their operations"
        },
        {
            "id": "CO2", 
            "description": "Implement and analyze linear data structures"
        }
    ]
}

def test_course_ingestion():
    """Test the course ingestion endpoint"""
    url = "http://localhost:8001/ingest-course"
    
    try:
        response = requests.post(url, json=test_course)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Course ingestion successful!")
            print(f"Course: {result['course_name']}")
            print(f"Units processed: {result['units_processed']}")
            print(f"Embeddings stored: {result['embeddings_stored']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8001/")
        if response.status_code == 200:
            print("✅ Server is running")
            print(response.json())
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running")

def test_question_evaluation():
    """Test the question evaluation endpoint"""
    url = "http://localhost:8001/evaluate-question"
    
    test_question = {
        "course_name": "Data Structures",
        "question": "Explain the implementation of a stack using arrays and discuss its time complexity"
    }
    
    try:
        response = requests.post(url, json=test_question)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Question evaluation successful!")
            print(f"Predicted CO: {result['predicted_co']}")
            print(f"Relevance Score: {result['relevance_score']}")
            print(f"Matched Unit: {result['matched_unit']}")
            print(f"Context: {result['matched_syllabus_context'][:100]}...")
            
            # Display explainability data if available
            if result.get('explanation') and result['explanation'].get('top_matches'):
                print("\n📊 Top Semantic Matches (Explainability):")
                for i, match in enumerate(result['explanation']['top_matches'], 1):
                    print(f"  {i}. Unit: {match['unit']} | CO: {match['co'][:50]}... | Score: {match['similarity']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_subtopic_suggestion():
    """Test the subtopic suggestion endpoint"""
    url = "http://localhost:8001/suggest-subtopics"
    
    test_data = {
        "course_name": "Data Structures",
        "unit_title": "Arrays and Linked Lists",
        "unit_content": "Introduction to arrays, dynamic arrays, singly linked lists, doubly linked lists, operations on linked lists"
    }
    
    try:
        response = requests.post(url, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Subtopic suggestion successful!")
            print(f"Unit: {result['unit']}")
            print(f"Suggested Subtopics: {result['suggested_subtopics']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_subtopic_confirmation():
    """Test the subtopic confirmation endpoint"""
    url = "http://localhost:8001/confirm-subtopics"
    
    test_data = {
        "course_name": "Data Structures",
        "unit_title": "Arrays and Linked Lists",
        "final_subtopics": [
            "Array declaration and initialization",
            "Dynamic array operations",
            "Singly linked list implementation",
            "Doubly linked list operations"
        ],
        "course_outcomes": [
            {"id": "CO1", "description": "Understand fundamental data structures"},
            {"id": "CO2", "description": "Implement linear data structures"}
        ]
    }
    
    try:
        response = requests.post(url, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Subtopic confirmation successful!")
            print(f"Message: {result['message']}")
            print(f"Unit: {result['unit']}")
            print(f"Subtopics processed: {result['subtopics_processed']}")
            print(f"Embeddings stored: {result['embeddings_stored']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing Question Intelligence System...")
    print("\n1. Health Check:")
    test_health_check()
    
    print("\n2. Course Ingestion:")
    test_course_ingestion()
    
    print("\n3. Question Evaluation:")
    test_question_evaluation()
    
    print("\n4. Subtopic Suggestion:")
    test_subtopic_suggestion()
    
    print("\n5. Subtopic Confirmation:")
    test_subtopic_confirmation()