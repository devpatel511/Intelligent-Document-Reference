import os
import shutil
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.vectordb.factory import get_vector_db

def run_quality_test():
    print("Loading embedding model (all-MiniLM-L6-v2) for Real Semantic Quality Test...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 1. Dataset: A mix of distinct topics to clearly separate clusters
    documents = [
        # Topic: Space
        "The sun is a star at the center of the solar system.",
        "Mars is often called the Red Planet because of its reddish appearance.",
        "Jupiter is the largest planet in our solar system.",
        # Topic: Coding
        "Python is a high-level, interpreted programming language known for readability.",
        "Rust guarantees memory safety without garbage collection.",
        "JavaScript is essential for web development and runs in the browser.",
        # Topic: Food
        "Sushi is a traditional Japanese dish of prepared vinegared rice.",
        "Pizza originated in Italy and consists of a round, flat base.",
        "Tacos are a traditional Mexican dish consisting of a corn or wheat tortilla.",
        # Distractors / Noise
        "The quick brown fox jumps over the lazy dog.",
        "Lorem ipsum dolor sit amet.",
    ]
    
    # 2. Queries with Expected Answers (Ground Truth Indices)
    test_cases = [
        ("What is the red planet?", 1), # Mars (Index 1)
        ("Tell me about a programming language with memory safety.", 4), # Rust (Index 4)
        ("Which planet is the biggest?", 2), # Jupiter (Index 2)
        ("Italian food with a flat base", 7), # Pizza (Index 7)
        ("Web coding language", 5), # JavaScript (Index 5)
    ]
    
    # Embed documents
    print(f"Generating embeddings for {len(documents)} documents...")
    embeddings = model.encode(documents).tolist()
    ids = [str(i) for i in range(len(documents))]
    metadatas = [{"text": doc} for doc in documents]
    
    # 3. Define Runner
    def test_db(db_type: str):
        print(f"\n--- Testing Retrieval Quality: {db_type.upper()} ---")
        db_path = f"quality_{db_type}.db"
        chroma_path = f"quality_chroma_{db_type}"
        
        # Cleanup prior runs
        if os.path.exists(db_path): os.remove(db_path)
        if os.path.exists(chroma_path): shutil.rmtree(chroma_path)
        
        try:
            # Init Driver
            if db_type == "sqlite":
                db = get_vector_db("sqlite", db_path=db_path)
            else:
                db = get_vector_db("chroma", persist_path=chroma_path)
            
            db.initialize()
            db.add_chunks(embeddings, metadatas, ids)
            
            # Run Queries
            correct_top1 = 0
            
            print(f"{'QUERY':<50} | {'RESULT':<40} | {'SCORE':<5}")
            print("-" * 105)

            for query_text, expected_index in test_cases:
                q_vec = model.encode(query_text).tolist()
                results = db.search(q_vec, limit=1)
                
                if not results:
                    print(f"{query_text:<50} | (No Results)")
                    continue
                    
                top_result = results[0]
                top_result_id = int(top_result['id'])
                score = top_result['score']
                retrieved_text = documents[top_result_id]
                
                # Truncate text for display
                display_text = (retrieved_text[:37] + '...') if len(retrieved_text) > 37 else retrieved_text
                
                is_correct = top_result_id == expected_index
                marker = "✅" if is_correct else "❌"
                
                print(f"{marker} {query_text:<48} | {display_text:<40} | {score:.4f}")
                
                if is_correct:
                    correct_top1 += 1
            
            accuracy = (correct_top1 / len(test_cases)) * 100
            print("-" * 105)
            print(f"Retrieval Accuracy: {accuracy:.0f}% ({correct_top1}/{len(test_cases)})")
            db.close()
            
        finally:
            # Cleanup
            if os.path.exists(db_path): os.remove(db_path)
            if os.path.exists(chroma_path): shutil.rmtree(chroma_path)

    # 4. Execute Comparison
    test_db("sqlite")
    test_db("chroma")

if __name__ == "__main__":
    run_quality_test()
