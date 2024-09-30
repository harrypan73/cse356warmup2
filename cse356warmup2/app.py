from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
from flask_mail import Mail, Message
from flask_session import Session
import os
import uuid
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Configure session to use filesystem (to persist sessions across server restarts)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)  # Initialize session

# Configure mail server
app.config['MAIL_SERVER'] = 'localhost'  # Configure your mail server
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None

mail = Mail(app)

# Course ID for header
COURSE_ID = '66d1c9697f77bf55c5004757'  # Replace with your actual course ID

# Path to users file
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

def send_verification_email(email, key):
    msg = Message('Email Verification', sender='noreply@yourdomain.com', recipients=[email])
    # Include the full link with parameters in the email text
    #verification_link = f'http://localhost:5000/verify?email={email}&key={key}'
    verification_link = f'http://130.245.136.146/verify?email={email}&key={key}'

    print(f"Sending email to {email} with link: {verification_link}")

    msg.body = f'Please verify your email by clicking the following link: {verification_link}'
    mail.send(msg)

@app.after_request
def add_header(response):
    response.headers['X-CSE356'] = COURSE_ID
    return response

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('register_page'))

    # if 'username' in session:
    #     return redirect(url_for('player'))
    # else:
    #     return redirect(url_for('login_page'))

@app.route('/adduser', methods=['POST'])
def add_user():
    users = load_users()  # Reload users data
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        email = data['email']

        if username in users:
            return jsonify({"error": True, "message": "Username already exists"}), 200
        if email in [user['email'] for user in users.values()]:
            return jsonify({"error": True, "message": "Email already exists"}), 200

        key = str(uuid.uuid4())
        users[username] = {'password': password, 'email': email, 'verified': False, 'key': key}
        save_users(users)
        send_verification_email(email, key)
        return jsonify({"message": "User created. Please check your email to verify."}), 200
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 200

@app.route('/verify', methods=['GET'])
def verify():
    users = load_users()  # Reload users data to get the latest changes

    email = request.args.get('email')
    key = request.args.get('key')

    for username, user in users.items():
        if user['email'] == email and user['key'] == key:
            user['verified'] = True
            save_users(users)
            return render_template('verify.html', message="Email verified successfully!")

    return render_template('verify.html', message="Invalid verification link")

@app.route('/login', methods=['POST'])
def login():
    users = load_users()  # Reload users data
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']

        user = users.get(username)
        if user and user['password'] == password and user['verified']:
            session['username'] = username
            return jsonify({"message": "Logged in successfully!"}), 200
        return jsonify({"error": True, "message": "Invalid credentials or unverified email."}), 200
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully!"}), 200

@app.route('/media/<path:filename>', methods=['GET'])
def media(filename):
    return send_from_directory('static/media', filename)

@app.route('/media/chunk_<int:bandwidth>_<int:segment_number>.m4s', methods=['GET'])
def serve_chunk(bandwidth, segment_number):
    filename = f"chunk_{bandwidth}_{segment_number}.m4s"
    return send_from_directory('static/media', filename)

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
