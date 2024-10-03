from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
from flask_mail import Mail, Message
from flask_session import Session
import os
import uuid
import json
from urllib.parse import urlencode
from urllib.parse import quote, unquote


app = Flask(__name__)
app.secret_key = 'your_secret_key'  

# Configure session to use filesystem (to persist sessions across server restarts)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')

Session(app)  

app.config['MAIL_SERVER'] = 'localhost'  # Configure your mail server
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None

mail = Mail(app)

COURSE_ID = '66d1c9697f77bf55c5004757'  

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()

@app.after_request
def add_header(response):
    response.headers['X-CSE356'] = COURSE_ID
    return response

from flask import make_response

@app.route('/', methods=['GET'])
def index():
    if 'username' in session:
        return redirect(url_for('player'))
    else:
        response = make_response(redirect(url_for('register_page')))
        response.data = jsonify({"status": "ERROR", "error": True, "message": "Unauthorized access. Please log in first."}).data
        response.status_code = 200
        return response

@app.route('/adduser', methods=['POST'])
def add_user():
    users = load_users()  
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        email = data['email']

        if username in users:
            return jsonify({"status": "ERROR", "error": True, "message": "Username already exists"}), 200

        if email in [user['email'] for user in users.values()]:
            return jsonify({"status": "ERROR", "error": True, "message": "Email already exists"}), 200

        # Generate a verification key and save the user
        key = str(uuid.uuid4()).replace('-', '')
        users[username] = {'password': password, 'email': email, 'verified': False, 'key': key}
        save_users(users)

        # Send verification email
        params = {'email': email, 'key': key}
        encoded_params = urlencode(params)
        verification_link = f'http://130.245.136.146/verify?{encoded_params}'

        msg = Message('Email Verification', sender='noreply@yourdomain.com', recipients=[email])
        msg.body = f'Please verify your email by clicking the following link:\n\n{verification_link}'
        msg.content_subtype = 'plain'  # Explicitly set the content subtype to plain text
        msg.charset = 'utf-8'           # Set charset to utf-8

        print(f"Sending email to {email} with link: {verification_link}")

        mail.send(msg)
        print("EMAIL SENT")
        
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "error": True, "message": str(e)}), 200

@app.route('/verify', methods=['GET'])
def verify():
    print(f"Request Args: {request.args}")

    users = load_users()  # Reload users data

    email = request.args.get('email')
    key = request.args.get('key')

    print(f"Received verification request for email: {email}, key: {key}")

    # print(key)

    if not email or not key:
        print("ERROR MISSING EMAIL OR KEY")
        return jsonify({"status": "ERROR", "error": True, "message": "Missing email or key in the request"}), 200

    print(f"Received verification request for email: {email}, key: {key}")
    print(f"Request URL: {request.url}")
    print(f"Request Args: {request.args}")

    for username, user in users.items():
        print(f"Checking user: {username}, email: {user['email']}, key: {user['key']}")
        print("HAHAHAHAHA")
        if user['email'] == email and user['key'] == key:
            print("BOOTYBOOTY")
            user['verified'] = True
            save_users(users)
            return jsonify({"status": "OK", "message": "Email verified successfully!"}), 200

    return jsonify({"status": "ERROR", "error": True, "message": "Invalid verification link"}), 200

@app.route('/login', methods=['POST'])
def login():
    users = load_users()  
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']

        user = users.get(username)
        if user and user['password'] == password and user['verified']:
            session['username'] = username
            return jsonify({"status": "OK", "message": "Logged in successfully!"}), 200
        return jsonify({"status": "ERROR", "error": True, "message": "Invalid credentials or unverified email."}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "error": True, "message": str(e)}), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"status": "OK", "message": "Logged out successfully!"}), 200

@app.route('/media/<path:filename>', methods=['GET'])
def media(filename):
    return send_from_directory('static/media', filename)

@app.route('/media/output.mpd', methods=['GET'])
def serve_manifest():
    return send_from_directory('static/media', 'output.mpd')

@app.route('/media/chunk_<int:bandwidth>_<int:segment_number>.m4s', methods=['GET'])
def serve_chunk(bandwidth, segment_number):
    try:
        filename = f"chunk_{bandwidth}_{segment_number}.m4s"
        return send_from_directory('static/media', filename)
    except Exception as e:
        return jsonify({"status": "ERROR", "error": True, "message": str(e)}), 200

@app.route('/player', methods=['GET'])
def player():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('mediaplayer.html')

@app.route('/login_page', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('adduser.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
