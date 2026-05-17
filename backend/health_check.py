import os
import sys
import sqlite3
import requests

def check_env():
    print("--- Environment Check ---")
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
        print(f"MISSING: {dotenv_path}")
    else:
        print(f"EXISTS: {dotenv_path}")
    
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)
    
    keys = ["GROQ_API_KEY", "GEMINI_API_KEY"]
    for key in keys:
        val = os.getenv(key)
        if val and val != "your_" + key.lower() + "_here":
            print(f"SET: {key}")
        else:
            print(f"NOT SET: {key}")

def check_db():
    print("\n--- Database Check ---")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'chatbot.db')
    if not os.path.exists(db_path):
        print(f"MISSING: {db_path} (Will be created on first run)")
    else:
        print(f"EXISTS: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            print(f"Tables found: {[t[0] for t in tables]}")
            conn.close()
        except Exception as e:
            print(f"DB ERROR: {e}")

def check_libraries():
    print("\n--- Library Check ---")
    libs = ["flask", "flask_cors", "groq", "langchain", "faiss", "google.generativeai"]
    for lib in libs:
        try:
            __import__(lib.replace("-", "_"))
            print(f"INSTALLED: {lib}")
        except ImportError:
            print(f"MISSING: {lib}")

def check_dataset():
    print("\n--- Dataset Check ---")
    dataset = "Cyberlaw_dataset.pdf"
    if os.path.exists(dataset):
        print(f"EXISTS: {dataset} ({os.path.getsize(dataset)} bytes)")
    else:
        print(f"MISSING: {dataset}")

def check_ollama():
    print("\n--- Ollama Check ---")
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=2)
        if res.status_code == 200:
            models = [m['name'] for m in res.json().get('models', [])]
            print(f"OLLAMA RUNNING. Models: {models}")
        else:
            print("OLLAMA OFFLINE (Status code non-200)")
    except Exception:
        print("OLLAMA OFFLINE (Connection refused)")

if __name__ == "__main__":
    check_env()
    check_db()
    check_libraries()
    check_dataset()
    check_ollama()
