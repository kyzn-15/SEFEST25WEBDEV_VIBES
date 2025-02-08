from flask import *
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Konfigurasi MongoDB
app.config["MONGO_URI"] = "mongodb+srv://win:123@wcluster.nlhup.mongodb.net/wcluster?retryWrites=true&w=majority"

mongo = PyMongo(app)

from pymongo import errors

try:
    if mongo.db is None:
        raise Exception("mongo.db is None. Check your MongoDB URI and connection settings.")
    mongo.db.list_collection_names()
    print("MongoDB Connected Successfully")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")



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

if __name__ == '__main__':
    app.run(debug=True)
