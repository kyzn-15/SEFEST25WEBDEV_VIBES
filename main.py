from flask import *
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Konfigurasi MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/friloapp"
mongo = PyMongo(app)

# ==================== ROUTES ====================

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
            "role": None,  # Default belum isi survey
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
    
    if not user:  # Jika user tidak ditemukan, logout dan minta login ulang
        flash("User not found, please log in again.", "error")
        return redirect(url_for('logout'))

    if user.get("role"):  # Jika sudah mengisi survey, langsung ke dashboard
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
            session.permanent = True  # Terapkan sesi
            session['username'] = username
            
            session['user'] = {
                "username": user['username'],
                "email": user['email'],
                "role": user.get('role', ''),
                "profile_data": user.get('profile_data', {}),
                "firstName": user.get('firstName', ''),
                "lastName": user.get('lastName', '')
            }

            if not user.get("role"):  # Jika belum isi survey, arahkan ke survey
                return redirect(url_for('survey'))

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

    # Ambil ulang data dari database jika session['user'] kosong atau tidak lengkap
    if 'user' not in session or not session['user'].get('role'):
        user = mongo.db.users.find_one({"username": session['username']})
        if not user:
            flash("User not found, please log in again.", "error")
            return redirect(url_for('logout'))
        
        # Isi ulang session['user']
        session['user'] = {
            "username": user['username'],
            "email": user['email'],
            "role": user.get('role', ''),  
            "profile_data": user.get('profile_data', {}),  
            "firstName": user.get('firstName', ''),  
            "lastName": user.get('lastName', '')  
        }

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

    # Extract data from JSON payload
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
    if 'username' not in session:
        flash("Page not found! Please login first.", "warning")
        return redirect(url_for('login'))
    
    flash("Page not found!", "error")
    return redirect(url_for('dashboard'))

    return jsonify({'success': True, 'redirect': url_for('dashboard')}), 200
if __name__ == '__main__':
    app.run(debug=True)
