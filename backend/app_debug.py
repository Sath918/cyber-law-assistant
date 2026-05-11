from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

from database import get_db_connection, init_db
from llm_service import generate_ai_response

frontend_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend'))
app = Flask(__name__)
app.secret_key = 'cyber_law_assistant_secret_key'
CORS(app)  # Enable CORS for frontend integration

@app.route('/')
def serve_index():
    return send_from_directory(frontend_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(frontend_folder, path)):
        return send_from_directory(frontend_folder, path)
    # Fallback to index.html for undefined frontend routes
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
            'profile_pic': user.get('profile_pic', 'default.png')
        }), 200
        
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
        
    # Get response from the AI model
    reply = generate_ai_response(message)
    
    # Optionally save to database if user is logged in
    chat_id = None
    if user_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
                     (user_id, message, reply))
        chat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
    return jsonify({'reply': reply, 'chat_id': chat_id}), 200

@app.route('/history', methods=['GET'])
def history():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    conn = get_db_connection()
    chats = conn.execute('SELECT id, message, response, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp ASC', (user_id,)).fetchall()
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

@app.route('/history/<int:chat_id>', methods=['DELETE'])
def delete_history(chat_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM chat_history WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Chat deleted successfully'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file element in request'}), 400
        
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not user_id:
        return jsonify({'error': 'User ID required to upload files'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        conn.execute('INSERT INTO files (user_id, filename, filepath) VALUES (?, ?, ?)',
                     (user_id, filename, filepath))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename
        }), 200


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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
