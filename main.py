from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, get_flashed_messages
from flask_pymongo import PyMongo
from flask_socketio import SocketIO, join_room, emit
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import random

# ==================== KONFIGURASI APLIKASI UTAMA ====================
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Gunakan satu MongoDB URL untuk semua kebutuhan
app.config["MONGO_URI"] = "mongodb+srv://kevin:admin123@kyzn.vrph9.mongodb.net/SEFEST25WEBDEV_VIBES?retryWrites=true&w=majority&appName=Kyzn"
mongo = PyMongo(app)

# Inisialisasi SocketIO (dengan async_mode threading agar kompatibel)
socketio = SocketIO(app, async_mode='threading')

# --- Koleksi untuk Fitur Chat ---
# Seluruh operasi chat menggunakan koleksi ini (di dalam database utama)
chat_users = mongo.db.chat_users         # Untuk data profil chat (user_id, contacts, dsb.)
chat_messages = mongo.db.chat_messages   # Untuk menyimpan pesan chat

# Fungsi pembantu: Pastikan setiap user memiliki profil chat
def ensure_chat_profile(username):
    chat_user = chat_users.find_one({"username": username})
    if not chat_user:
        while True:
            new_id = str(random.randint(1000, 999999))
            if not chat_users.find_one({'user_id': new_id}):
                break
        chat_users.insert_one({
            'username': username,
            'password': '',  # Password tidak dipakai untuk chat
            'user_id': new_id,
            'contacts': []   # Daftar kontak awal kosong
        })
        chat_user = chat_users.find_one({"username": username})
    return chat_user

from pymongo import errors

try:
    if mongo.db is None:
        raise Exception("mongo.db is None. Check your MongoDB URI and connection settings.")
    mongo.db.list_collection_names()
    print("MongoDB Connected Successfully")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")



# ==================== ROUTES UTAMA (Login, Signup, Survey, Dashboard, dsb.) ====================
@app.route('/')
@app.route('/homepage')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash("Passwords don't match!", "error")
            return redirect(url_for('signup'))
        if mongo.db.users.find_one({"username": username}):
            flash("Username already exists!", "error")
            return redirect(url_for('signup'))
        if mongo.db.users.find_one({"email": email}):
            flash("Email already registered!", "error")
            return redirect(url_for('signup'))
        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
            "role": None,  # Belum mengisi survey
            "profile_data": {}
        })
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html', messages=get_flashed_messages(with_categories=True))

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    user = mongo.db.users.find_one({"username": session['username']})
    if not user:
        flash("User not found, please log in again.", "error")
        return redirect(url_for('logout'))
    if user.get("role"):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        role = request.form.get('role')
        industry = request.form.get('industry')
        job = request.form.get('job')
        avatar = request.form.get('avatar')
        if not role:
            flash("Please select a role!", "error")
            return redirect(url_for('survey'))
        profile_data = {}
        if role == "worker":
            profile_data['skills'] = request.form.getlist('skills')
        elif role == "hirer":
            profile_data['requirements'] = request.form.get('requirements')
        profile_data.update({
            "industry": industry or "Not specified",
            "job": job or "Not specified",
            "avatar": avatar or "default.png"
        })

        # Update MongoDB with the survey data
        mongo.db.users.update_one(
            {"username": session['username']},
            {"$set": {"role": role, "profile_data": profile_data}}
        )
        flash("Survey completed successfully!", "success")
        
        # Redirect to the dashboard after survey submission
        return redirect(url_for('dashboard'))
    return render_template('survey.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['username'] = username
            session['user'] = {
                "username": user['username'],
                "email": user['email'],
                "role": user.get('role', ''),
                "profile_data": user.get('profile_data', {}),
                "firstName": user.get('firstName', ''),
                "lastName": user.get('lastName', '')
            }
            if not user.get("role"):
                return redirect(url_for('survey'))
            # Pastikan profil chat sudah ada, simpan user_id chat ke session
            chat_user = ensure_chat_profile(username)
            session['user_id'] = chat_user['user_id']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    # Selalu ambil data user dari MongoDB
    user = mongo.db.users.find_one({"username": session['username']})
    if not user:
        flash("User not found, please log in again.", "error")
        return redirect(url_for('logout'))

    # Perbarui session['user'] dengan data yang terbaru dari database
    session['user'] = {
        "username": user['username'],
        "email": user['email'],
        "role": user.get('role', ''),
        "profile_data": user.get('profile_data', {}),
        "firstName": user.get('firstName', ''),
        "lastName": user.get('lastName', '')
    }

    projects = list(mongo.db.projects.find().sort("created_at", -1))
    
    # Ambil daftar industri unik dari data user
    industries = mongo.db.users.distinct("profile_data.industry")
    
    return render_template('dashboard.html', user=session['user'], projects=projects, industries=industries)
    # Perbarui data user jika perlu
    if 'user' not in session or not session['user'].get('role'):
        user = mongo.db.users.find_one({"username": session['username']})
        if not user:
            flash("User not found, please log in again.", "error")
            return redirect(url_for('logout'))
        session['user'] = {
            "username": user['username'],
            "email": user['email'],
            "role": user.get('role', ''),
            "profile_data": user.get('profile_data', {}),
            "firstName": user.get('firstName', ''),
            "lastName": user.get('lastName', '')
        }
    # Pastikan session['user_id'] sudah ada
    if 'user_id' not in session:
        chat_user = ensure_chat_profile(session['username'])
        session['user_id'] = chat_user['user_id']
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/api/submit-survey', methods=['POST'])
def submit_survey():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    role = data.get('role')
    industry = data.get('industry')
    job = data.get('job')
    avatar = data.get('avatar')
    first_name = data.get('firstName')
    last_name = data.get('lastName')

    # Basic validation
    if not role:
        return jsonify({'error': 'Role is required'}), 400

    # Prepare profile data
    profile_data = {
        'industry': industry or 'Not specified',
        'job': job or 'Not specified',
        'avatar': avatar or 'default.png'
    }

    # Update user document in MongoDB
    mongo.db.users.update_one(
        {'username': session['username']},
        {'$set': {
            'role': role,
            'firstName': first_name,
            'lastName': last_name,
            'profile_data': profile_data
        }}
    )

    # **Tambahkan return statement di sini**
    return jsonify({'success': True, 'message': 'Survey submitted successfully!'}), 200

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# ==================== ROUTES & SOCKETIO UNTUK FITUR CHAT ====================
@app.route('/chat')
def chat():
    if 'username' not in session or 'user_id' not in session:
        return redirect(url_for('login'))
    
    flash("Page not found!", "error")
    return redirect(url_for('dashboard'))


@app.route('/create_project', methods=['POST'])
def create_project():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))

    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')
    bidang = request.form.get('bidang')

    if not title or not description or not price or not bidang:
        flash("Semua field wajib diisi!", "error")
        return redirect(url_for('dashboard'))

    new_project = {
        "title": title,
        "description": description,
        "price": float(price),
        "bidang": bidang,
        "created_at": datetime.utcnow(),
        "created_by": session['username'],  # simpan username pembuat proyek
        "avatar": session['user']['profile_data']['avatar'],
        "status": "open"  # status proyek, misalnya: open, in-progress, completed
    }
    
    # Masukkan data ke koleksi 'projects'
    mongo.db.projects.insert_one(new_project)
    flash("Project created successfully!", "success")
    return redirect(url_for('dashboard'))

from bson.objectid import ObjectId

@app.route('/id-project')
def project_detail():
    # Ambil parameter 'id' dari URL
    project_id = request.args.get('id')
    if not project_id:
        flash("Project ID is missing.", "error")
        return redirect(url_for('dashboard'))
    
    try:
        # Konversi ke ObjectId dan ambil data project
        project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
    except Exception as e:
        flash("Invalid project ID.", "error")
        return redirect(url_for('dashboard'))
    
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('dashboard'))
    
    return render_template('project_detail.html', project=project)

@app.route('/update_project', methods=['POST'])
def update_project():
    project_id = request.form.get('project_id')
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')
    bidang = request.form.get('bidang')
    status = request.form.get('status')
    
    # Lakukan validasi data jika perlu
    
    mongo.db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {
            "title": title,
            "description": description,
            "price": float(price),
            "bidang": bidang,
            "status": status,
            "updated_at": datetime.utcnow()
        }}
    )
    flash("Project updated successfully!", "success")
    return redirect(url_for('project_detail', id=project_id))

# Ambil data profil chat user dan daftar kontak dari koleksi chat_users
    chat_user = chat_users.find_one({'user_id': session['user_id']})
    contacts = []
    if chat_user and 'contacts' in chat_user:
        for contact_id in chat_user['contacts']:
            contact_doc = chat_users.find_one({'user_id': contact_id})
            if contact_doc:
                contacts.append({
                    'user_id': contact_doc['user_id'],
                    'contact_username': contact_doc['username']
                })
    return render_template('chat.html', username=session['username'], user_id=session['user_id'], contacts=contacts)

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(session['user_id'])
        emit('status', {'msg': f'{session["username"]} has connected'}, room=session['user_id'])

@socketio.on('private_message')
def handle_private_message(data):
    sender_username = session['username']
    sender_id = session['user_id']
    receiver_id = data.get('receiver')
    message = data.get('message')
    if not message:
        return  # Jangan proses pesan kosong
    print(f"[DEBUG] private_message: from {sender_id} to {receiver_id}: {message}")
    timestamp = datetime.now()
    # Simpan pesan ke koleksi chat_messages
    message_data = {
        'sender_id': sender_id,
        'sender_username': sender_username,
        'receiver_id': receiver_id,
        'message': message,
        'timestamp': timestamp
    }
    chat_messages.insert_one(message_data)
    formatted_time = timestamp.strftime("%H:%M")
    # Tambahkan pengirim ke daftar kontak penerima (jika belum ada)
    result = chat_users.update_one(
        {'user_id': receiver_id},
        {'$addToSet': {'contacts': sender_id}}
    )
    if result.modified_count > 0:
        sender_doc = chat_users.find_one({'user_id': sender_id})
        if sender_doc:
            emit('contact_added', {
                'contact_id': sender_doc['user_id'],
                'contact_username': sender_doc['username']
            }, room=receiver_id)
    # Emit pesan ke pengirim
    emit('new_message', {
        'sender': sender_username,
        'sender_id': sender_id,
        'message': message,
        'timestamp': formatted_time,
        'is_me': True
    }, room=sender_id)
    # Emit pesan ke penerima
    emit('new_message', {
        'sender': sender_username,
        'sender_id': sender_id,
        'message': message,
        'timestamp': formatted_time,
        'is_me': False
    }, room=receiver_id)

@socketio.on('get_history')
def handle_get_history(data):
    my_id = session['user_id']
    contact_id = data.get('contact')
    query = {
        '$or': [
            {'sender_id': my_id, 'receiver_id': contact_id},
            {'sender_id': contact_id, 'receiver_id': my_id}
        ]
    }
    history = list(chat_messages.find(query).sort('timestamp', 1))
    formatted_history = []
    for msg in history:
        formatted_history.append({
            'sender': msg['sender_username'],
            'message': msg['message'],
            'timestamp': msg['timestamp'].strftime("%H:%M"),
            'is_me': msg['sender_id'] == my_id
        })
    emit('message_history', formatted_history)

@socketio.on('add_contact')
def handle_add_contact(data):
    contact_id = data.get('contact_id')
    current_user_id = session.get('user_id')
    print(f"[DEBUG] add_contact: current_user_id={current_user_id}, contact_id={contact_id}")
    if not contact_id:
        emit('contact_error', {'msg': 'No contact ID provided.'}, room=current_user_id)
        return
    if contact_id == current_user_id:
        emit('contact_error', {'msg': 'You cannot add yourself as a contact.'}, room=current_user_id)
        return
    # Cari kontak di koleksi chat_users
    contact = chat_users.find_one({'user_id': contact_id})
    if not contact:
        emit('contact_error', {
            'msg': f'User with ID {contact_id} not found. Please ensure the user has logged in at least once.'
        }, room=current_user_id)
        return
    update_result = chat_users.update_one(
        {'user_id': current_user_id},
        {'$addToSet': {'contacts': contact_id}}
    )
    # Emit event contact_added jika update berhasil (atau dokumen sudah cocok)
    if update_result.modified_count > 0 or update_result.matched_count > 0:
        emit('contact_added', {
            'contact_id': contact['user_id'],
            'contact_username': contact['username']
        }, room=current_user_id)
    else:
        emit('contact_error', {'msg': 'Failed to add contact.'}, room=current_user_id)

# ==================== MAIN ====================
if __name__ == '__main__':
    app.run(debug=True)
    socketio.run(app, debug=True)
