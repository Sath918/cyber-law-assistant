from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import shutil
from typing import Optional

# Relative package imports
from .database import get_db_connection, init_db
from .llm_service import generate_ai_response, generate_ai_response_stream
from .rag_pipeline import add_document_to_user_index, process_session_document, rebuild_session_index

# Determine paths relative to workspace root
base_workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
frontend_folder = os.path.abspath(os.path.join(base_workspace_dir, 'frontend'))
UPLOAD_FOLDER = os.path.join(base_workspace_dir, 'uploads')
PROFILE_PICS_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database when app starts
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def serve_index():
    return FileResponse(os.path.join(frontend_folder, 'index.html'))

@app.post('/register')
async def register(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'error': 'Please provide username, email, and password'}, status_code=400)
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return JSONResponse({'error': 'Please provide username, email, and password'}, status_code=400)
        
    hashed_pw = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_pw))
        conn.commit()
        return JSONResponse({'message': 'User registered successfully'}, status_code=201)
    except sqlite3.IntegrityError:
        return JSONResponse({'error': 'Username or email already exists'}, status_code=400)
    finally:
        conn.close()

@app.post('/login')
async def login(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'error': 'Please provide username and password'}, status_code=400)
        
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return JSONResponse({'error': 'Please provide username and password'}, status_code=400)
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        return JSONResponse({
            'message': 'Login successful',
            'user_id': user['id'],
            'username': user['username'],
            'profile_pic': dict(user).get('profile_pic', 'default.png')
        }, status_code=200)
        
    return JSONResponse({'error': 'Invalid credentials'}, status_code=401)

@app.post('/chat')
async def chat(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'error': 'No message provided'}, status_code=400)
        
    user_id = data.get('user_id')
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    language_mode = data.get('language', 'en')
    attached_files = data.get('attached_files', [])
    
    if not message:
        return JSONResponse({'error': 'No message provided'}, status_code=400)
        
    # Get history for context
    history = []
    if user_id and session_id:
        conn = get_db_connection()
        chats = conn.execute('SELECT message, response FROM chat_history WHERE user_id = ? AND session_id = ? ORDER BY timestamp ASC', (user_id, session_id)).fetchall()
        conn.close()
        history = [dict(chat) for chat in chats]

    # Get response from the AI model
    reply = generate_ai_response(message, language_mode, history, user_id=user_id, session_id=session_id)
    
    # Save to database if user is logged in
    chat_id = None
    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Save attached files to history first
            for filename in attached_files:
                cursor.execute('INSERT INTO chat_history (user_id, session_id, message, response) VALUES (?, ?, ?, ?)',
                             (user_id, session_id, f"FILE_ATTACHMENT:|:{filename}:|:Ready", ""))
            
            cursor.execute('INSERT INTO chat_history (user_id, session_id, message, response) VALUES (?, ?, ?, ?)',
                         (user_id, session_id, message, reply))
            chat_id = cursor.lastrowid
            conn.commit()
            conn.close()
        except Exception as e:
            print("DB Save Error in chat:", e)
        
    return JSONResponse({'reply': reply, 'chat_id': chat_id, 'session_id': session_id}, status_code=200)

@app.post('/chat_stream')
async def chat_stream(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'error': 'No message provided'}, status_code=400)
        
    user_id = data.get('user_id')
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    language_mode = data.get('language', 'en')
    attached_files = data.get('attached_files', [])
    
    if not message:
        return JSONResponse({'error': 'No message provided'}, status_code=400)
        
    def generate():
        full_reply = ""
        
        # Save attached files to history first
        if user_id and session_id and attached_files:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                for filename in attached_files:
                    cursor.execute('INSERT INTO chat_history (user_id, session_id, message, response) VALUES (?, ?, ?, ?)',
                                 (user_id, session_id, f"FILE_ATTACHMENT:|:{filename}:|:Ready", ""))
                conn.commit()
                conn.close()
            except Exception as e:
                print("Error saving attached files to history:", e)
        
        # Get history for context if user is logged in
        history = []
        if user_id and session_id:
            try:
                conn = get_db_connection()
                chats = conn.execute('SELECT message, response FROM chat_history WHERE user_id = ? AND session_id = ? ORDER BY timestamp ASC', (user_id, session_id)).fetchall()
                conn.close()
                history = [dict(chat) for chat in chats]
            except Exception as e:
                print("History Load Error:", e)

        for chunk in generate_ai_response_stream(message, language_mode, history, user_id=user_id, session_id=session_id):
            full_reply += chunk
            yield chunk
            
        if user_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO chat_history (user_id, session_id, message, response) VALUES (?, ?, ?, ?)',
                             (user_id, session_id, message, full_reply.strip()))
                conn.commit()
                conn.close()
            except Exception as e:
                print("DB Save Error:", e)
                
    return StreamingResponse(generate(), media_type='text/plain')

@app.get('/sessions')
async def get_sessions(user_id: Optional[int] = None):
    if not user_id:
        return JSONResponse({'error': 'User ID is required'}, status_code=400)
        
    conn = get_db_connection()
    sessions = conn.execute('''
        SELECT session_id, MIN(message) as first_message, MAX(timestamp) as last_updated
        FROM chat_history
        WHERE user_id = ?
        GROUP BY session_id
        ORDER BY last_updated DESC
    ''', (user_id,)).fetchall()
    conn.close()
    
    sessions_data = []
    for s in sessions:
        sessions_data.append({
            'session_id': s['session_id'],
            'first_message': s['first_message'],
            'last_updated': s['last_updated']
        })
        
    return JSONResponse({'sessions': sessions_data}, status_code=200)

@app.get('/history')
async def history(user_id: Optional[int] = None, session_id: Optional[str] = None):
    if not user_id or not session_id:
        return JSONResponse({'error': 'User ID and Session ID are required'}, status_code=400)
        
    conn = get_db_connection()
    chats = conn.execute('SELECT id, message, response, timestamp FROM chat_history WHERE user_id = ? AND session_id = ? ORDER BY timestamp ASC', (user_id, session_id)).fetchall()
    conn.close()
    
    history_data = []
    for chat in chats:
        history_data.append({
            'id': chat['id'],
            'message': chat['message'],
            'response': chat['response'],
            'timestamp': chat['timestamp']
        })
        
    return JSONResponse({'history': history_data}, status_code=200)

@app.delete('/history/{session_id}')
async def delete_history(session_id: str, user_id: Optional[int] = None):
    if not user_id:
        return JSONResponse({'error': 'User ID required'}, status_code=400)
    conn = get_db_connection()
    conn.execute('DELETE FROM chat_history WHERE session_id = ? AND user_id = ?', (session_id, user_id))
    conn.commit()
    conn.close()
    return JSONResponse({'message': 'Session deleted successfully'}, status_code=200)

@app.post('/history/trim/{session_id}')
async def trim_history(session_id: str, request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'error': 'User ID and index required'}, status_code=400)
        
    user_id = data.get('user_id')
    index = data.get('index')
    
    if not user_id or index is None:
        return JSONResponse({'error': 'User ID and index required'}, status_code=400)
        
    conn = get_db_connection()
    chats = conn.execute('SELECT timestamp FROM chat_history WHERE session_id = ? AND user_id = ? ORDER BY timestamp ASC LIMIT 1 OFFSET ?', (session_id, user_id, index)).fetchone()
    
    if chats:
        cutoff_timestamp = chats['timestamp']
        conn.execute('DELETE FROM chat_history WHERE session_id = ? AND user_id = ? AND timestamp >= ?', (session_id, user_id, cutoff_timestamp))
        conn.commit()
    conn.close()
    return JSONResponse({'message': 'History trimmed successfully'}, status_code=200)

@app.post('/upload')
async def upload_file(
    file: UploadFile = File(None),
    user_id: Optional[int] = Form(None),
    session_id: str = Form("default")
):
    if not file:
        return JSONResponse({'error': 'No file element in request'}, status_code=400)
        
    if file.filename == '':
        return JSONResponse({'error': 'No selected file'}, status_code=400)
        
    if not user_id:
        return JSONResponse({'error': 'User ID required to upload files'}, status_code=400)
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.pdf', '.docx', '.txt']:
        return JSONResponse({'error': 'Unsupported file format. Only PDF, DOCX, and TXT files are allowed.'}, status_code=400)

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO files (user_id, session_id, filename, filepath, status) VALUES (?, ?, ?, ?, ?)',
                 (user_id, session_id, filename, filepath, 'uploading'))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    def generate_progress():
        import json
        from .rag_pipeline import process_session_document
        
        # 1. State: Extracting
        yield json.dumps({"status": "extracting", "message": "Extracting text...", "id": file_id, "filename": filename}) + "\n"
        
        # 2. State: Indexing
        yield json.dumps({"status": "indexing", "message": "Indexing document...", "id": file_id, "filename": filename}) + "\n"
        
        success, result = process_session_document(user_id, session_id, filepath, filename)
        
        if success:
            yield json.dumps({"status": "ready", "message": "Ready for questions.", "id": file_id, "filename": filename}) + "\n"
        else:
            yield json.dumps({"status": "error", "message": f"Processing failed: {result}", "id": file_id, "filename": filename}) + "\n"
            
    return StreamingResponse(generate_progress(), media_type='text/plain')

@app.get('/sessions/{session_id}/files')
async def get_session_files(session_id: str):
    conn = get_db_connection()
    files = conn.execute(
        'SELECT id, filename, status, upload_date FROM files WHERE session_id = ? ORDER BY upload_date ASC',
        (session_id,)
    ).fetchall()
    conn.close()
    
    files_data = []
    for f in files:
        files_data.append({
            'id': f['id'],
            'filename': f['filename'],
            'status': f['status'],
            'upload_date': f['upload_date']
        })
    return JSONResponse({'files': files_data}, status_code=200)

@app.delete('/files/{file_id}')
async def delete_file(file_id: int):
    conn = get_db_connection()
    file_row = conn.execute('SELECT filepath, session_id FROM files WHERE id = ?', (file_id,)).fetchone()
    
    if not file_row:
        conn.close()
        return JSONResponse({'error': 'File not found'}, status_code=404)
        
    filepath = file_row['filepath']
    session_id = file_row['session_id']
    
    conn.execute('DELETE FROM files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error removing physical file {filepath}: {e}")
            
    from .rag_pipeline import rebuild_session_index
    rebuild_session_index(session_id)
    
    return JSONResponse({'message': 'File deleted and index updated successfully'}, status_code=200)

@app.get('/profile/{user_id}')
async def get_profile(user_id: int):
    conn = get_db_connection()
    user = conn.execute('SELECT username, email, profile_pic FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return JSONResponse(dict(user), status_code=200)
    return JSONResponse({'error': 'User not found'}, status_code=404)

@app.post('/profile/update')
async def update_profile(
    user_id: int = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: Optional[str] = Form(None),
    profile_pic: Optional[UploadFile] = File(None)
):
    conn = get_db_connection()
    try:
        if password:
            hashed_pw = generate_password_hash(password)
            conn.execute('UPDATE users SET username=?, email=?, password=? WHERE id=?', 
                         (username, email, hashed_pw, user_id))
        else:
            conn.execute('UPDATE users SET username=?, email=? WHERE id=?', 
                         (username, email, user_id))
        
        profile_pic_name = None
        if profile_pic and profile_pic.filename != '':
            profile_pic_name = secure_filename(f"user_{user_id}_{profile_pic.filename}")
            filepath = os.path.join(PROFILE_PICS_FOLDER, profile_pic_name)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(profile_pic.file, buffer)
            conn.execute('UPDATE users SET profile_pic=? WHERE id=?', (profile_pic_name, user_id))
        
        conn.commit()
        return JSONResponse({'message': 'Profile updated successfully', 'profile_pic': profile_pic_name}, status_code=200)
    except sqlite3.IntegrityError:
        return JSONResponse({'error': 'Username or email already exists'}, status_code=400)
    finally:
        conn.close()

@app.get('/uploads/profiles/{filename}')
async def serve_profile_pic(filename: str):
    file_path = os.path.join(PROFILE_PICS_FOLDER, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return JSONResponse({'error': 'File not found'}, status_code=404)

@app.get('/{path:path}')
async def serve_static(path: str):
    file_path = os.path.join(frontend_folder, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    # Fallback to index.html for SPA routing
    return FileResponse(os.path.join(frontend_folder, 'index.html'))
