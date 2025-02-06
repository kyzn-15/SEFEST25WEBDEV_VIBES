from flask import *
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/friloapp"
mongo = PyMongo(app)

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
        username = request.form['username']
        email = request.form['email']
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
            "created_at": datetime.utcnow()
        })
        
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = mongo.db.users.find_one({"username": username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
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
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)