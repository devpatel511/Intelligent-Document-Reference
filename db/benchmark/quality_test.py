import os

from sentence_transformers import SentenceTransformer

from db import UnifiedDatabase


def run_quality_test() -> None:
    """Run a qualitative semantic search test using real sentences."""
    print("Loading embedding model (all-MiniLM-L6-v2) for Semantic Test...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # --- Test Set 1: Disambiguation (Rigorous) ---
    documents = [
        # 0-2: Python (Language)
        "Python is a clean, interpreted language emphasizing readability.",
        "Pip is the standard package manager for installing Python libraries.",
        "Flask and Django are popular web frameworks for Python.",
        # 3-5: Python (Snake)
        "Pythons are non-venomous constrictors found in Africa and Asia.",
        "The ball python is a popular small snake pet.",
        "Large pythons constrict their prey until respiration stops.",
        # 6-8: Java (Language)
        "Java is a class-based, object-oriented language meant to have few dependencies.",
        "The JVM allows Java code to run on any device.",
        "Spring Boot makes it easy to create stand-alone Java applications.",
        # 9-11: Java (Coffee)
        "Java is a colloquial term for coffee, originating from the island of Java.",
        "Espresso is a concentrated coffee brewed with high pressure.",
        "A latte consists of espresso and steamed milk.",
        # 12-14: JavaScript (Web)
        "JavaScript runs in the browser to make webpages interactive.",
        "Node.js allows developers to run JavaScript on the server.",
        "React is a library for building user interfaces in JavaScript.",
    ]

    # Query format: (Question, [List of Valid Indices], Label)
    test_cases = [
        ("How to install python packages?", [1], "Python Code"),
        ("Dangerous snakes in Africa", [3, 5], "Python Animal"),
        ("Web development with flask", [2], "Python Code"),
        ("Brewing strong coffee", [10, 9], "Coffee"),
        ("Object oriented programming with virtual machine", [6, 7], "Java Code"),
        ("Code running in browser", [12], "JS Code"),
        ("Pet snake", [4], "Python Animal"),
        ("Backend javascript server", [13], "JS Code"),
    ]

    print(f"Generating embeddings for {len(documents)} documents...")
    embeddings = model.encode(documents).tolist()

    # Map to UnifiedDB format
    chunks = []
    for i, doc in enumerate(documents):
        # We use stringified index as UUID equivalent for verification
        chunks.append({"id": str(i), "text_content": doc, "chunk_index": 0})

    print(f"\n{'='*40}")
    print("Testing Retrieval Quality: UnifiedSQLite")
    print(f"{'='*40}")

    db_path = "quality_unified.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    try:
        db = UnifiedDatabase(db_path)
        file_id = db.register_file("quality.txt", "hash", 0, 0.0)
        version_id = db.create_version(file_id, "v1")

        db.add_document(file_id, version_id, chunks, embeddings)

        k = 3
        hit_1 = 0
        hit_3 = 0

        # Header
        print(f"{'QUERY':<50} | {'TOP 1':<25} | {'1?':<3} | {'ALL?':<6}")
        print("-" * 95)

        for query, expected_idxs, label in test_cases:
            q_vec = model.encode(query).tolist()
            results = db.search(q_vec, limit=k)

            # Retrieved IDs
            found_ids = [int(r["chunk_id"]) for r in results] if results else []

            # Metric 1: Top-1 Accuracy
            top1_ok = False
            if found_ids and found_ids[0] in expected_idxs:
                top1_ok = True
                hit_1 += 1

            # Metric 2: Full Recall
            found_valid = set(found_ids) & set(expected_idxs)
            full_recall = len(found_valid) == len(expected_idxs)
            if full_recall:
                hit_3 += 1

            # Display
            top_txt = documents[found_ids[0]] if found_ids else "None"
            top_display = (top_txt[:22] + "...") if len(top_txt) > 22 else top_txt

            m1 = "✅" if top1_ok else "❌"
            m3 = "✅" if full_recall else f"⚠️ {len(found_valid)}/{len(expected_idxs)}"

            print(f"{query:<50} | {top_display:<25} | {m1:<3} | {m3:<6}")

        print("-" * 95)
        print(f"Top-1 Accuracy: {(hit_1/len(test_cases))*100:.0f}%")
        print(f"Perfect Recall: {(hit_3/len(test_cases))*100:.0f}%")

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    run_quality_test()
