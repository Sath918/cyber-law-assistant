import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'chatbot.db')

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            profile_pic TEXT DEFAULT 'default.png'
        )
    ''')
    
    # Safely migrate existing table to include profile_pic
    try:
        c.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT 'default.png'")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    # chat_history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT DEFAULT 'default',
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    try:
        c.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT DEFAULT 'default'")
    except sqlite3.OperationalError:
        pass
    
    # files table
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Safely migrate files table to include session_id, status, and file_hash
    try:
        c.execute("ALTER TABLE files ADD COLUMN session_id TEXT DEFAULT 'default'")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE files ADD COLUMN status TEXT DEFAULT 'ready'")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE files ADD COLUMN file_hash TEXT")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
