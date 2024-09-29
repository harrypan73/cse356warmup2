from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
from flask_mail import Mail, Message
import os
import uuid
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAIL_SERVER'] = 'localhost'  # Configure your mail server
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None

mail = Mail(app)

users = {}  # In-memory storage for users

def send_verification_email(email, key):
    msg = Message('Email Verification', sender='noreply@yourdomain.com', recipients=[email])
    msg.body = f'Please verify your email by clicking the following link: http://localhost:5000/verify?email={email}&key={key}'
    mail.send(msg)

@app.route('/adduser', methods=['POST'])
def add_user():
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
    send_verification_email(email, key)
    return jsonify({"message": "User created. Please check your email to verify."}), 200

@app.route('/verify', methods=['GET'])
def verify():
    email = request.args.get('email')
    key = request.args.get('key')

    for user in users.values():
        if user['email'] == email and user['key'] == key:
            user['verified'] = True
            return jsonify({"message": "Email verified successfully!"}), 200

    return jsonify({"error": True, "message": "Invalid verification link"}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = users.get(username)
    if user and user['password'] == password and user['verified']:
        session['username'] = username
        return jsonify({"message": "Logged in successfully!"}), 200
    return jsonify({"error": True, "message": "Invalid credentials or unverified email."}), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully!"}), 200

@app.route('/media/<path:filename>', methods=['GET'])
def media(filename):
    return send_from_directory('static/media', filename)

@app.route('/player', methods=['GET'])
def player():
    return render_template('player.html')

if __name__ == '__main__':
    app.run(debug=True)