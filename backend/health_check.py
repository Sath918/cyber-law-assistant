import os
import sys
import sqlite3
import requests

def check_env():
    print("--- Environment Check ---")
    env_path = ".env" if os.path.exists(".env") else "backend/.env"
    if not os.path.exists(env_path):
        print("MISSING: .env file (checked root and backend/)")
    else:
        print(f"EXISTS: .env file at {env_path}")
        
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    keys = ["GROQ_API_KEY", "GEMINI_API_KEY"]
    for key in keys:
        val = os.getenv(key)
        if val and val != "your_" + key.lower() + "_here" and not val.startswith("your_"):
            print(f"SET: {key}")
        else:
            print(f"NOT SET: {key}")

def check_db():
    print("\n--- Database Check ---")
    db_path = "database/chatbot.db"
    if not os.path.exists(db_path):
        db_path = "backend/database/chatbot.db"
    if not os.path.exists(db_path) and os.path.exists("../database/chatbot.db"):
        db_path = "../database/chatbot.db"
        
    if not os.path.exists(db_path):
        print(f"MISSING: chatbot.db (Checked paths database/chatbot.db and backend/database/chatbot.db)")
    else:
        print(f"EXISTS: chatbot.db at {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            print(f"Tables found: {[t[0] for t in tables]}")
            conn.close()
        except Exception as e:
            print(f"DB ERROR: {e}")

def check_libraries():
    print("\n--- Library Check ---")
    libs = ["fastapi", "uvicorn", "multipart", "groq", "langchain", "faiss", "google.generativeai"]
    for lib in libs:
        try:
            __import__(lib.replace("-", "_"))
            print(f"INSTALLED: {lib}")
        except ImportError:
            print(f"MISSING: {lib}")

def check_dataset():
    print("\n--- Dataset Check ---")
    dataset = "backend/Cyberlaw_dataset.pdf" if os.path.exists("backend/Cyberlaw_dataset.pdf") else "Cyberlaw_dataset.pdf"
    if not os.path.exists(dataset) and os.path.exists("../backend/Cyberlaw_dataset.pdf"):
        dataset = "../backend/Cyberlaw_dataset.pdf"
        
    if os.path.exists(dataset):
        print(f"EXISTS: {dataset} ({os.path.getsize(dataset)} bytes)")
    else:
        print(f"MISSING: Cyberlaw_dataset.pdf (Checked backend/ and root)")

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

def check_groq():
    print("\n--- Groq API Connection Check ---")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here" or api_key.startswith("your_"):
        print("GROQ KEY NOT CONFIGURED IN ENV")
        return
        
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            timeout=5
        )
        print("GROQ API CONNECTION SUCCESS: Received ping response.")
    except Exception as e:
        print(f"GROQ API CONNECTION FAILED: {e}")

if __name__ == "__main__":
    check_env()
    check_db()
    check_libraries()
    check_dataset()
    check_ollama()
    check_groq()
