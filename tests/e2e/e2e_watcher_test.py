import sqlite3
import time
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_test():
    db_path = os.path.abspath("file_registry.db")
    print(f"Connecting to DB: {db_path}")
    
    # 1. Clean up old test data
    test_folder = os.path.abspath("test_watch_folder")
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)
        
    # Clean DB config
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM monitor_config WHERE path = ?", (test_folder,))
        conn.execute("DELETE FROM processing_queue")
        conn.commit()

    print("State cleared.")
    
    # 2. Add Watch Path
    print(f"Adding watch path: {test_folder}")
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO monitor_config (path, excluded_files, is_active)
            VALUES (?, ?, 1)
        """, (test_folder, json.dumps([])))
        conn.commit()
    
    print("Waiting 7 seconds for watcher to sync...")
    time.sleep(7)
    
    # 3. Create File
    file_path = os.path.join(test_folder, "test_doc.txt")
    print(f"Creating file: {file_path}")
    with open(file_path, "w") as f:
        f.write("Hello World")
        
    print("Waiting 2 seconds for event...")
    time.sleep(2)
    
    # 4. Check Queue
    found = False
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM processing_queue")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Queue Item: {row['event_type']} - {row['file_path']}")
            if os.path.abspath(row['file_path']) == os.path.abspath(file_path):
                found = True
        
    if found:
        print("\nSUCCESS: Event found in queue!")
    else:
        print("\nFAILURE: NO event found in queue.")
        print("Check if watcher service is running in another terminal: 'python watcher/main.py'")

if __name__ == "__main__":
    run_test()
