from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret'
DATABASE = 'quiz.db'

# ---------------- DATABASE ----------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    from create_db import conn
    # Database already created via create_db.py
    pass

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, password))
            db.commit()
            return redirect(url_for('login'))
        except:
            return render_template('register.html', error="Email already registered!")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('quiz_selection'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- USER FLOW ----------------
@app.route('/quiz_selection')
def quiz_selection():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    quizzes = db.execute("SELECT * FROM quizzes").fetchall()
    return render_template('quiz_selection.html', quizzes=quizzes)

@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    questions = db.execute("SELECT * FROM questions WHERE quiz_id=?", (quiz_id,)).fetchall()
    if request.method == 'POST':
        score = 0
        for q in questions:
            selected = request.form.get(str(q['id']))
            if selected == q['correct_option']:
                score += 1
        db.execute("INSERT INTO results (user_id, quiz_id, score) VALUES (?, ?, ?)",
                   (session['user_id'], quiz_id, score))
        db.commit()
        return render_template('result.html', score=score, total=len(questions))
    return render_template('quiz.html', questions=questions)

# ---------------- ADMIN FLOW ----------------
@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    quizzes = db.execute("""
        SELECT q.id, q.name,
               COUNT(DISTINCT qs.id) AS total_questions,
               COUNT(DISTINCT r.id) AS total_attempts
        FROM quizzes q
        LEFT JOIN questions qs ON q.id = qs.quiz_id
        LEFT JOIN results r ON q.id = r.quiz_id
        GROUP BY q.id
    """).fetchall()
    questions = db.execute("""
        SELECT qs.*, q.name as quiz_name
        FROM questions qs
        JOIN quizzes q ON qs.quiz_id = q.id
    """).fetchall()
    return render_template('admin_dashboard.html', quizzes=quizzes, questions=questions)

@app.route('/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        db = get_db()
        db.execute("INSERT INTO quizzes (name) VALUES (?)", (name,))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_quiz.html')

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    quizzes = db.execute("SELECT * FROM quizzes").fetchall()
    if request.method == 'POST':
        data = (
            request.form['question'],
            request.form['option1'],
            request.form['option2'],
            request.form['option3'],
            request.form['option4'],
            request.form['correct_option'],
            request.form['quiz_id']
        )
        db.execute('''
            INSERT INTO questions (question, option1, option2, option3, option4, correct_option, quiz_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
        db.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_question.html', quizzes=quizzes)

# ---------------- DELETE QUIZ ----------------
@app.route('/delete_quiz/<int:quiz_id>')
def delete_quiz(quiz_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    # Delete all questions and results for this quiz
    db.execute("DELETE FROM questions WHERE quiz_id = ?", (quiz_id,))
    db.execute("DELETE FROM results WHERE quiz_id = ?", (quiz_id,))
    db.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

# ---------------- RESULTS ----------------
@app.route('/admin_results')
def admin_results():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    results = db.execute('''
        SELECT u.username, q.name as quiz_name, r.score
        FROM results r
        JOIN users u ON r.user_id = u.id
        JOIN quizzes q ON r.quiz_id = q.id
    ''').fetchall()
    return render_template('admin_results.html', results=results)

@app.route('/user_results')
def user_results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    results = db.execute('''
        SELECT q.name as quiz_name, r.score
        FROM results r
        JOIN quizzes q ON r.quiz_id = q.id
        WHERE r.user_id=?
    ''', (session['user_id'],)).fetchall()
    return render_template('user_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
