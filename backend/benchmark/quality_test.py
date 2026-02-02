import os
import shutil
from sentence_transformers import SentenceTransformer
from backend.vectordb.factory import get_vector_db


def run_quality_test():
    print(
        "Loading embedding model (all-MiniLM-L6-v2) for Real Semantic Quality Test..."
    )
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # --- Test Set 1: Disambiguation (Rigorous) ---
    # Intentionally overlapping terms to test semantic understanding
    # We test Polysemy (Words with multiple meanings: Python, Java)
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
    # We use lists of valid indices because sometimes query applies to multiple docs
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
    ids = [str(i) for i in range(len(documents))]
    metadatas = [{"text": doc} for doc in documents]

    def test_db(db_type: str):
        print(f"\n{'='*40}")
        print(f"Testing Retrieval Quality: {db_type.upper()}")
        print(f"{'='*40}")

        db_path = f"quality_{db_type}.db"
        chroma_path = f"quality_chroma_{db_type}"

        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)

        try:
            if db_type == "sqlite":
                db = get_vector_db("sqlite", db_path=db_path)
            else:
                db = get_vector_db("chroma", persist_path=chroma_path)

            db.initialize()
            db.add_chunks(embeddings, metadatas, ids)

            k = 3
            hits_at_1 = 0
            hits_at_3 = 0

            print(
                f"{'QUERY':<50} | {'TOP 1 DOC':<30} | {'TOP 1?':<6} | {'ALL FOUND?':<10}"
            )
            print("-" * 105)

            for query_text, valid_indices, label in test_cases:
                q_vec = model.encode(query_text).tolist()
                results = db.search(q_vec, limit=k)

                retrieved_ids = [int(r["id"]) for r in results] if results else []

                # Metric 1: Is the absolute top result correct?
                is_top1_good = False
                if retrieved_ids and retrieved_ids[0] in valid_indices:
                    is_top1_good = True
                    hits_at_1 += 1

                # Metric 2: Rigorous Multi-hit check
                # Did we find ALL expected documents within the top K?
                # (For overlapping topics, providing just 1 answer when 2 exist is increasingly considered a "fail" in RAG)
                found_valid_ids = set(retrieved_ids) & set(valid_indices)
                is_perfect_recall = len(found_valid_ids) == len(valid_indices)

                if is_perfect_recall:
                    hits_at_3 += 1

                # Display Logic
                if retrieved_ids:
                    top_text = documents[retrieved_ids[0]]
                    top_text_display = (
                        (top_text[:27] + "...") if len(top_text) > 27 else top_text
                    )
                else:
                    top_text_display = "None"

                m1 = "✅" if is_top1_good else "❌"
                m_perfect = (
                    "✅"
                    if is_perfect_recall
                    else f"⚠️ ({len(found_valid_ids)}/{len(valid_indices)})"
                )

                print(
                    f"{query_text:<50} | {top_text_display:<30} | {m1:<6} | {m_perfect:<10}"
                )

            print("-" * 105)
            print(
                f"Top-1 Accuracy: {(hits_at_1/len(test_cases))*100:.0f}% (First result is relevant)"
            )
            print(
                f"Perfect Recall: {(hits_at_3/len(test_cases))*100:.0f}% (Found ALL relevant docs in Top-3)"
            )

            db.close()

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(chroma_path):
                shutil.rmtree(chroma_path)

    test_db("sqlite")
    test_db("chroma")


if __name__ == "__main__":
    run_quality_test()
