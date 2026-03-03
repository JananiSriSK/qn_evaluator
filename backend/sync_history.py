"""
Sync current history.json to MongoDB
Run this after evaluating questions to move them to MongoDB
"""

from services.mongodb_history_repository import MongoDBHistoryRepository
from pathlib import Path
import json

def sync_history(user_id="1"):
    """Sync history.json to MongoDB"""
    
    # Load from file
    history_file = Path("data") / user_id / "history.json"
    if not history_file.exists():
        print(f"No history file found for user {user_id}")
        return
    
    with open(history_file, 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    # Save to MongoDB
    repo = MongoDBHistoryRepository()
    repo.save_history(user_id, history_data)
    
    print(f"[OK] Synced history to MongoDB")
    print(f"  - Single questions: {len(history_data.get('single_questions', []))}")
    print(f"  - PDF evaluations: {len(history_data.get('pdf_evaluations', []))}")
    
    if history_data.get('single_questions'):
        last_q = history_data['single_questions'][0]
        print(f"\n  Last question: {last_q['question'][:60]}...")
        print(f"  Timestamp: {last_q['timestamp']}")

if __name__ == '__main__':
    import sys
    user_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    
    print("=" * 60)
    print("  Sync History to MongoDB")
    print("=" * 60)
    
    sync_history(user_id)
    
    print("\n[SUCCESS] Check MongoDB Compass:")
    print("  1. Open Compass -> mongodb://localhost:27017/")
    print("  2. Database: qn_evaluator")
    print("  3. Collection: history")
    print("  4. Query: { user_id: \"1\" }")
