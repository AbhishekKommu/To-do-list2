import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HTML Page Routes ---
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html', username=current_user.username)

# --- Authentication REST APIs ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    hashed_pw = generate_password_hash(data['password'], method='scrypt')
    new_user = User(username=data['username'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if not user or not check_password_hash(user.password, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401

    login_user(user)
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

# --- Task CRUD REST APIs ---
@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return jsonify([t.to_dict() for t in tasks]), 200

@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    task = Task(title=data['title'], user_id=current_user.id)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json()
    if 'title' in data:
        task.title = data['title']
    if 'completed' in data:
        task.completed = data['completed']

    db.session.commit()
    return jsonify(task.to_dict()), 200

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)