from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

from database import get_db_connection, init_db
from llm_service import generate_ai_response, generate_ai_response_stream
from rag_pipeline import add_document_to_user_index
from flask import Response

frontend_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend'))
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'cyber_law_assistant_secret_key')
CORS(app)  # Enable CORS for frontend integration

@app.route('/')
def serve_index():
    return send_from_directory(frontend_folder, 'index.html')




UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Database when app starts
init_db()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Please provide username, email, and password'}), 400
        
    hashed_pw = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_pw))
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Please provide username and password'}), 400
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        return jsonify({
            'message': 'Login successful',
            'user_id': user['id'],
            'username': user['username'],
            'profile_pic': dict(user).get('profile_pic', 'default.png')
        }), 200
        
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    language_mode = data.get('language', 'en')
    attached_files = data.get('attached_files', [])
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
        
    # Get history for context
    history = []
    if user_id and session_id:
        conn = get_db_connection()
        chats = conn.execute('SELECT message, response FROM chat_history WHERE user_id = ? AND session_id = ? ORDER BY timestamp ASC', (user_id, session_id)).fetchall()
        conn.close()
        history = [dict(chat) for chat in chats]

    # Get response from the AI model
    reply = generate_ai_response(message, language_mode, history, user_id=user_id, session_id=session_id)
    
    # Optionally save to database if user is logged in
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
        
    return jsonify({'reply': reply, 'chat_id': chat_id, 'session_id': session_id}), 200

@app.route('/chat_stream', methods=['POST'])
def chat_stream():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    session_id = data.get('session_id', 'default')
    language_mode = data.get('language', 'en')
    attached_files = data.get('attached_files', [])
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
        
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
                
    return Response(generate(), mimetype='text/plain')

@app.route('/sessions', methods=['GET'])
def get_sessions():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
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
        
    return jsonify({'sessions': sessions_data}), 200

@app.route('/history', methods=['GET'])
def history():
    user_id = request.args.get('user_id')
    session_id = request.args.get('session_id')
    
    if not user_id or not session_id:
        return jsonify({'error': 'User ID and Session ID are required'}), 400
        
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
        
    return jsonify({'history': history_data}), 200

@app.route('/history/<session_id>', methods=['DELETE'])
def delete_history(session_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    conn = get_db_connection()
    conn.execute('DELETE FROM chat_history WHERE session_id = ? AND user_id = ?', (session_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Session deleted successfully'}), 200

@app.route('/history/trim/<session_id>', methods=['POST'])
def trim_history(session_id):
    data = request.get_json()
    user_id = data.get('user_id')
    index = data.get('index')
    
    if not user_id or index is None:
        return jsonify({'error': 'User ID and index required'}), 400
        
    conn = get_db_connection()
    chats = conn.execute('SELECT timestamp FROM chat_history WHERE session_id = ? AND user_id = ? ORDER BY timestamp ASC LIMIT 1 OFFSET ?', (session_id, user_id, index)).fetchone()
    
    if chats:
        cutoff_timestamp = chats['timestamp']
        conn.execute('DELETE FROM chat_history WHERE session_id = ? AND user_id = ? AND timestamp >= ?', (session_id, user_id, cutoff_timestamp))
        conn.commit()
    conn.close()
    return jsonify({'message': 'History trimmed successfully'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file element in request'}), 400
        
    file = request.files['file']
    user_id = request.form.get('user_id')
    session_id = request.form.get('session_id', 'default')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not user_id:
        return jsonify({'error': 'User ID required to upload files'}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.pdf', '.docx', '.txt']:
        return jsonify({'error': 'Unsupported file format. Only PDF, DOCX, and TXT files are allowed.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO files (user_id, session_id, filename, filepath, status) VALUES (?, ?, ?, ?, ?)',
                 (user_id, session_id, filename, filepath, 'uploading'))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    def generate_progress():
        import json
        from rag_pipeline import process_session_document
        
        # 1. State: Extracting
        yield json.dumps({"status": "extracting", "message": "Extracting text...", "id": file_id, "filename": filename}) + "\n"
        
        # 2. State: Indexing
        yield json.dumps({"status": "indexing", "message": "Indexing document...", "id": file_id, "filename": filename}) + "\n"
        
        success, result = process_session_document(user_id, session_id, filepath, filename)
        
        if success:
            yield json.dumps({"status": "ready", "message": "Ready for questions.", "id": file_id, "filename": filename}) + "\n"
        else:
            yield json.dumps({"status": "error", "message": f"Processing failed: {result}", "id": file_id, "filename": filename}) + "\n"
            
    return Response(generate_progress(), mimetype='text/plain')

@app.route('/sessions/<session_id>/files', methods=['GET'])
def get_session_files(session_id):
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
    return jsonify({'files': files_data}), 200

@app.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    conn = get_db_connection()
    file_row = conn.execute('SELECT filepath, session_id FROM files WHERE id = ?', (file_id,)).fetchone()
    
    if not file_row:
        conn.close()
        return jsonify({'error': 'File not found'}), 404
        
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
            
    from rag_pipeline import rebuild_session_index
    rebuild_session_index(session_id)
    
    return jsonify({'message': 'File deleted and index updated successfully'}), 200


PROFILE_PICS_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')
os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)

@app.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT username, email, profile_pic FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return jsonify(dict(user)), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/profile/update', methods=['POST'])
def update_profile():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not user_id or not username or not email:
        return jsonify({'error': 'Missing required fields'}), 400
        
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
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                profile_pic_name = secure_filename(f"user_{user_id}_{file.filename}")
                filepath = os.path.join(PROFILE_PICS_FOLDER, profile_pic_name)
                file.save(filepath)
                conn.execute('UPDATE users SET profile_pic=? WHERE id=?', (profile_pic_name, user_id))
        
        conn.commit()
        return jsonify({'message': 'Profile updated successfully', 'profile_pic': profile_pic_name}), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    finally:
        conn.close()

@app.route('/uploads/profiles/<filename>')
def serve_profile_pic(filename):
    return send_from_directory(PROFILE_PICS_FOLDER, filename)

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(frontend_folder, path)):
        return send_from_directory(frontend_folder, path)
    # Fallback to index.html for undefined frontend routes
    return send_from_directory(frontend_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
