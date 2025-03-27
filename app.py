from flask import Flask, render_template, redirect, request, session, url_for
from models import db, User, Subject, Chapter, Quiz, Question, Score
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizmaster.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secretkey"

def get_db_connection():
    conn = sqlite3.connect("quizmaster.db")
    conn.row_factory = sqlite3.Row
    return conn

db.init_app(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the credentials match the admin credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin_dashboard')

        # Check if the credentials match a regular user
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect('/user_dashboard')

        return "Invalid credentials!"
    
    return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        qualification = request.form["qualification"]
        dob = request.form["dob"]

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "User already exists!"

        # Insert new user
        new_user = User(username=username, password=password, full_name=full_name, qualification=qualification, dob=dob)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))  # Redirect to login after successful registration

    return render_template("register.html")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    subjects = Subject.query.all()
    return render_template('user_dashboard.html', subjects=subjects)

@app.route('/view_chapters/<int:subject_id>')
def view_chapters(subject_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    subject = Subject.query.get(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('view_chapters.html', subject=subject, chapters=chapters)

@app.route('/view_quizzes/<int:chapter_id>')
def view_quizzes(chapter_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    chapter = Chapter.query.get(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('view_quizzes.html', chapter=chapter, quizzes=quizzes)

@app.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    if 'user_id' not in session:
        return redirect('/login')

    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    # Check if the user has already completed the quiz
    existing_score = Score.query.filter_by(quiz_id=quiz_id, user_id=session['user_id']).first()
    if existing_score:
        return render_template('quiz_completed.html', quiz=quiz)

    if request.method == 'POST':
        score = 0
        for question in questions:
            user_answer = request.form.get(f'question_{question.id}')
            if user_answer == question.correct_option:
                score += 1
        
        new_score = Score(quiz_id=quiz_id, user_id=session['user_id'], total_scored=score)
        db.session.add(new_score)
        db.session.commit()

        return redirect('/user_dashboard')

    return render_template('attempt_quiz.html', quiz=quiz, questions=questions)

@app.route('/view_scores')
def view_scores():
    if 'user_id' not in session:
        return redirect('/login')

    scores = Score.query.filter_by(user_id=session['user_id']).all()
    return render_template('view_scores.html', scores=scores)

@app.route('/view_results/<int:quiz_id>')
def view_results(quiz_id):
    if 'user_id' not in session:
        return redirect('/login')

    quiz = Quiz.query.get(quiz_id)
    scores = Score.query.filter_by(quiz_id=quiz_id, user_id=session['user_id']).all()
    return render_template('results.html', quiz=quiz, scores=scores)

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin_dashboard')
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin_login')
    subjects = Subject.query.all()
    return render_template('admin_dashboard.html', subjects=subjects)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/add_subject', methods=['POST'])
def add_subject():
    if 'admin' not in session:
        return redirect('/admin_login')
    name = request.form['name']
    description = request.form['description']
    new_subject = Subject(name=name, description=description)
    db.session.add(new_subject)
    db.session.commit()
    return redirect('/admin_dashboard')

@app.route('/delete_subject/<int:id>')
def delete_subject(id):
    if 'admin' not in session:
        return redirect('/admin_login')
    subject = Subject.query.get(id)
    if subject:
        db.session.delete(subject)
        db.session.commit()
    return redirect('/admin_dashboard')

@app.route('/manage_chapters/<int:subject_id>')
def manage_chapters(subject_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    subject = Subject.query.get(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('manage_chapters.html', subject=subject, chapters=chapters)

@app.route('/add_chapter/<int:subject_id>', methods=['POST'])
def add_chapter(subject_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    name = request.form['name']
    new_chapter = Chapter(name=name, subject_id=subject_id)
    db.session.add(new_chapter)
    db.session.commit()
    return redirect(f'/manage_chapters/{subject_id}')

@app.route('/delete_chapter/<int:id>')
def delete_chapter(id):
    if 'admin' not in session:
        return redirect('/admin_login')
    chapter = Chapter.query.get(id)
    if chapter:
        db.session.delete(chapter)
        db.session.commit()
    return redirect('/admin_dashboard')

@app.route('/manage_quizzes/<int:chapter_id>')
def manage_quizzes(chapter_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    chapter = Chapter.query.get(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('manage_quizzes.html', chapter=chapter, quizzes=quizzes)

@app.route('/add_quiz/<int:chapter_id>', methods=['POST'])
def add_quiz(chapter_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    date_of_quiz = request.form['date_of_quiz']
    time_duration = request.form['time_duration']
    new_quiz = Quiz(chapter_id=chapter_id, date_of_quiz=date_of_quiz, time_duration=time_duration)
    db.session.add(new_quiz)
    db.session.commit()
    return redirect(f'/manage_quizzes/{chapter_id}')

@app.route('/delete_quiz/<int:id>')
def delete_quiz(id):
    if 'admin' not in session:
        return redirect('/admin_login')
    quiz = Quiz.query.get(id)
    if quiz:
        db.session.delete(quiz)
        db.session.commit()
    return redirect('/admin_dashboard')

@app.route('/manage_questions/<int:quiz_id>', methods=['GET', 'POST'])
def manage_questions(quiz_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    
    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == 'POST':
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']

        new_question = Question(
            quiz_id=quiz_id,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )
        db.session.add(new_question)
        db.session.commit()
        return redirect(f'/manage_questions/{quiz_id}')

    return render_template('manage_questions.html', quiz=quiz, questions=questions)

@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
    return redirect(f'/manage_questions/{question.quiz_id}')

if __name__ == '__main__':
    app.run(debug=True)
