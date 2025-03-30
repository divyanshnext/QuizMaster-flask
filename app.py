# Import required libraries and modules
from flask import Flask, render_template, redirect, request, session, url_for, flash, jsonify
from models import db, User, Subject, Chapter, Quiz, Question, Score
import sqlite3
from sqlalchemy import func, or_
from datetime import datetime
import calendar
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

# Initialize Flask application
app = Flask(__name__)

# Configure application settings
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizmaster.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Database connection helper function
def get_db_connection():
    conn = sqlite3.connect("quizmaster.db")
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database with app
db.init_app(app)

# Route: Home page
@app.route('/')
def home():
    return render_template('index.html')

# Route: User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        # Verify user credentials using password hashing
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/user_dashboard')
        else:
            flash('Invalid username or password!', 'error')
    return render_template('login.html')

# Route: User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        qualification = request.form['qualification']
        dob = request.form['dob']
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect('/register')
            
        # Create new user with hashed password
        user = User(
            username=username,
            password=generate_password_hash(password),
            full_name=full_name,
            qualification=qualification,
            dob=dob
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    return render_template('register.html')

# Route: User logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

# Route: User dashboard
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    # Get all upcoming quizzes across all subjects and chapters
    upcoming_quizzes = db.session.query(
        Quiz, Chapter, Subject,
        func.count(Question.id).label('question_count')
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).outerjoin(
        Question, Quiz.id == Question.quiz_id
    ).group_by(
        Quiz.id
    ).order_by(
        Quiz.date_of_quiz
    ).all()

    return render_template('user_dashboard.html', upcoming_quizzes=upcoming_quizzes)

# Route: View chapters for a subject
@app.route('/view_chapters/<int:subject_id>')
def view_chapters(subject_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    subject = Subject.query.get(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('view_chapters.html', subject=subject, chapters=chapters)

# Route: View quizzes for a chapter
@app.route('/view_quizzes/<int:chapter_id>')
def view_quizzes(chapter_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    chapter = Chapter.query.get(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('view_quizzes.html', chapter=chapter, quizzes=quizzes)

# Route: Attempt a quiz
@app.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    if 'user_id' not in session:
        return redirect('/login')

    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    # Check if user has already completed the quiz
    existing_score = Score.query.filter_by(quiz_id=quiz_id, user_id=session['user_id']).first()
    if existing_score:
        return render_template('quiz_completed.html', quiz=quiz)

    if request.method == 'POST':
        try:
            # Calculate score based on correct answers
            score = 0
            total_questions = len(questions)
            
            for question in questions:
                user_answer = request.form.get(f'question_{question.id}')
                if user_answer and user_answer == question.correct_option:
                    score += 1
            
            # Save the score
            new_score = Score(quiz_id=quiz_id, user_id=session['user_id'], total_scored=score)
            db.session.add(new_score)
            db.session.commit()
            
            flash(f'Quiz completed! Your score: {score}/{total_questions}', 'success')
            return redirect(url_for('view_results', quiz_id=quiz_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error submitting quiz. Please try again.', 'error')
            print(f"Error: {str(e)}")  # For debugging
            return redirect(url_for('attempt_quiz', quiz_id=quiz_id))

    return render_template('attempt_quiz.html', quiz=quiz, questions=questions)

# Route: View user's scores
@app.route('/view_scores')
def view_scores():
    if 'user_id' not in session:
        return redirect('/login')

    scores = Score.query.filter_by(user_id=session['user_id']).all()
    return render_template('view_scores.html', scores=scores)

# Route: View detailed results for a quiz
@app.route('/view_results/<int:quiz_id>')
def view_results(quiz_id):
    if 'user_id' not in session:
        return redirect('/login')

    quiz = Quiz.query.get_or_404(quiz_id)
    score = Score.query.filter_by(quiz_id=quiz_id, user_id=session['user_id']).first_or_404()
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Get user's answers for each question
    user_answers = {}
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        if user_answer:
            user_answers[question.id] = user_answer
    
    return render_template('results.html', 
                         quiz=quiz, 
                         score=score, 
                         questions=questions,
                         user_answers=user_answers)

# Admin credentials (should be moved to environment variables in production)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Route: Admin login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    # If admin is already logged in, redirect to dashboard
    if session.get('admin'):
        return redirect('/admin_dashboard')
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            flash('Welcome Admin!', 'success')
            return redirect('/admin_dashboard')
        else:
            flash('Invalid admin credentials!', 'error')
            return redirect('/admin_login')
    return render_template('admin_login.html')

# Route: Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin_login')
    subjects = Subject.query.all()
    users = User.query.all()
    return render_template('admin_dashboard.html', subjects=subjects, users=users)

# Route: Admin logout
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/')

# Route: Add new subject
@app.route('/add_subject', methods=['POST'])
def add_subject():
    if 'admin' not in session:
        flash('Please login as admin first!', 'error')
        return redirect('/admin_login')
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Subject name is required!', 'error')
            return redirect('/admin_dashboard')
            
        # Check if subject already exists
        if Subject.query.filter_by(name=name).first():
            flash('A subject with this name already exists!', 'error')
            return redirect('/admin_dashboard')
            
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding subject. Please try again.', 'error')
    return redirect('/admin_dashboard')

# Route: Delete a subject
@app.route('/delete_subject/<int:id>')
def delete_subject(id):
    if 'admin' not in session:
        return redirect('/admin_login')
    subject = Subject.query.get(id)
    if subject:
        db.session.delete(subject)
        db.session.commit()
    return redirect('/admin_dashboard')

# Route: Manage chapters for a subject
@app.route('/manage_chapters/<int:subject_id>')
def manage_chapters(subject_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    subject = Subject.query.get(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('manage_chapters.html', subject=subject, chapters=chapters)

# Route: Add new chapter
@app.route('/add_chapter/<int:subject_id>', methods=['POST'])
def add_chapter(subject_id):
    if 'admin' not in session:
        flash('Please login as admin first!', 'error')
        return redirect('/admin_login')
    try:
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Chapter name is required!', 'error')
            return redirect(f'/manage_chapters/{subject_id}')
            
        # Check if chapter already exists in this subject
        if Chapter.query.filter_by(name=name, subject_id=subject_id).first():
            flash('A chapter with this name already exists in this subject!', 'error')
            return redirect(f'/manage_chapters/{subject_id}')
            
        new_chapter = Chapter(name=name, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding chapter. Please try again.', 'error')
    return redirect(f'/manage_chapters/{subject_id}')

# Route: Delete a chapter
@app.route('/delete_chapter/<int:id>')
def delete_chapter(id):
    if 'admin' not in session:
        return redirect('/admin_login')
    chapter = Chapter.query.get(id)
    if chapter:
        db.session.delete(chapter)
        db.session.commit()
    return redirect('/admin_dashboard')

# Route: Manage quizzes for a chapter
@app.route('/manage_quizzes/<int:chapter_id>')
def manage_quizzes(chapter_id):
    if 'admin' not in session:
        return redirect('/admin_login')
    chapter = Chapter.query.get(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('manage_quizzes.html', chapter=chapter, quizzes=quizzes)

# Route: Add new quiz
@app.route('/add_quiz/<int:chapter_id>', methods=['POST'])
def add_quiz(chapter_id):
    if 'admin' not in session:
        flash('Please login as admin first!', 'error')
        return redirect('/admin_login')
    try:
        date_of_quiz = request.form.get('date_of_quiz', '').strip()
        time_duration = request.form.get('time_duration', '').strip()
        
        if not date_of_quiz or not time_duration:
            flash('Both date and duration are required!', 'error')
            return redirect(f'/manage_quizzes/{chapter_id}')
            
        try:
            time_duration = int(time_duration)
            if time_duration < 1 or time_duration > 180:
                raise ValueError
        except ValueError:
            flash('Duration must be between 1 and 180 minutes!', 'error')
            return redirect(f'/manage_quizzes/{chapter_id}')
            
        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration
        )
        db.session.add(new_quiz)
        db.session.commit()
        flash('Quiz added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding quiz. Please try again.', 'error')
    return redirect(f'/manage_quizzes/{chapter_id}')

# Route: Delete a quiz
@app.route('/delete_quiz/<int:id>')
def delete_quiz(id):
    if 'admin' not in session:
        return redirect('/admin_login')
    quiz = Quiz.query.get(id)
    if quiz:
        db.session.delete(quiz)
        db.session.commit()
    return redirect('/admin_dashboard')

# Route: Manage questions for a quiz
@app.route('/manage_questions/<int:quiz_id>', methods=['GET', 'POST'])
def manage_questions(quiz_id):
    if 'admin' not in session:
        flash('Please login as admin first!', 'error')
        return redirect('/admin_login')
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == 'POST':
        try:
            # Get form data
            question_statement = request.form.get('question_statement', '').strip()
            option1 = request.form.get('option1', '').strip()
            option2 = request.form.get('option2', '').strip()
            option3 = request.form.get('option3', '').strip()
            option4 = request.form.get('option4', '').strip()
            correct_option = request.form.get('correct_option', '').strip()

            # Validate inputs
            if not all([question_statement, option1, option2, option3, option4, correct_option]):
                flash('All fields are required!', 'error')
                return redirect(url_for('manage_questions', quiz_id=quiz_id))

            # Validate correct option is a number between 1 and 4
            try:
                correct_option = int(correct_option)
                if correct_option < 1 or correct_option > 4:
                    raise ValueError
            except ValueError:
                flash('Correct option must be a number between 1 and 4!', 'error')
                return redirect(url_for('manage_questions', quiz_id=quiz_id))

            # Create new question
            new_question = Question(
                quiz_id=quiz_id,
                question_statement=question_statement,
                option1=option1,
                option2=option2,
                option3=option3,
                option4=option4,
                correct_option=str(correct_option)  # Store as string in database
            )
            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', 'success')

        except Exception as e:
            db.session.rollback()
            flash('Error adding question. Please try again.', 'error')
            print(f"Error: {str(e)}")  # For debugging

        return redirect(url_for('manage_questions', quiz_id=quiz_id))

    return render_template('manage_questions.html', quiz=quiz, questions=questions)

# Route: Delete a question
@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'admin' not in session:
        flash('Please login as admin first!', 'error')
        return redirect('/admin_login')
    
    try:
        question = Question.query.get_or_404(question_id)
        quiz_id = question.quiz_id
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting question. Please try again.', 'error')
        print(f"Error: {str(e)}")  # For debugging
    
    return redirect(url_for('manage_questions', quiz_id=quiz_id))

# Route: Admin summary/analytics
@app.route('/admin_summary')
def admin_summary():
    if 'admin' not in session:
        return redirect('/admin_login')
    
    # Get all subjects
    subjects = Subject.query.all()
    subject_names = [subject.name for subject in subjects]
    
    # Calculate top scores and attempts for each subject
    top_scores = []
    attempts_count = []
    
    for subject in subjects:
        chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        chapter_ids = [chapter.id for chapter in chapters]
        quizzes = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).all()
        quiz_ids = [quiz.id for quiz in quizzes]
        
        if quiz_ids:
            top_score = db.session.query(func.max(Score.total_scored)).filter(Score.quiz_id.in_(quiz_ids)).scalar() or 0
            attempts = Score.query.filter(Score.quiz_id.in_(quiz_ids)).count()
        else:
            top_score = 0
            attempts = 0
            
        top_scores.append(top_score)
        attempts_count.append(attempts)
    
    return render_template('admin_summary.html', 
                         subjects=subject_names,
                         top_scores=top_scores,
                         attempts_count=attempts_count)

# Route: User summary/analytics
@app.route('/user_summary')
def user_summary():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    # Get all subjects and their quiz counts
    subjects = Subject.query.all()
    subject_names = [subject.name for subject in subjects]
    quiz_counts = []
    
    for subject in subjects:
        chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        chapter_ids = [chapter.id for chapter in chapters]
        quiz_count = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).count()
        quiz_counts.append(quiz_count)
    
    # Get monthly attempts data
    current_month = datetime.now().month
    months = []
    monthly_attempts = []
    
    for i in range(6):  # Last 6 months
        month_num = ((current_month - i - 1) % 12) + 1
        month_name = calendar.month_name[month_num]
        months.insert(0, month_name)
        attempts = Score.query.filter_by(user_id=user_id).count()
        monthly_attempts.insert(0, attempts)
    
    return render_template('user_summary.html',
                         subjects=subject_names,
                         quiz_counts=quiz_counts,
                         months=months,
                         monthly_attempts=monthly_attempts)

# Route: Admin search functionality
@app.route('/admin_search')
def admin_search():
    if 'admin' not in session:
        return redirect('/admin_login')
    
    query = request.args.get('q', '')
    
    # Search across users, subjects, and quizzes
    users = User.query.filter(or_(
        User.username.ilike(f'%{query}%'),
        User.full_name.ilike(f'%{query}%')
    )).all()
    
    subjects = Subject.query.filter(or_(
        Subject.name.ilike(f'%{query}%'),
        Subject.description.ilike(f'%{query}%')
    )).all()
    
    chapters = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).all()
    chapter_ids = [chapter.id for chapter in chapters]
    quizzes = Quiz.query.filter(or_(
        Quiz.chapter_id.in_(chapter_ids),
        Quiz.date_of_quiz.ilike(f'%{query}%')
    )).all()
    
    return render_template('admin_search.html', 
                         users=users, 
                         subjects=subjects, 
                         quizzes=quizzes,
                         query=query)

# Route: View question details
@app.route('/view_question/<int:question_id>')
def view_question(question_id):
    if 'admin' not in session:
        flash('Please login as admin first!', 'error')
        return redirect('/admin_login')
    
    try:
        question = Question.query.get_or_404(question_id)
        return jsonify({
            'id': question.id,
            'statement': question.question_statement,
            'option1': question.option1,
            'option2': question.option2,
            'option3': question.option3,
            'option4': question.option4,
            'correct_option': question.correct_option
        })
    except Exception as e:
        print(f"Error: {str(e)}")  # For debugging
        return jsonify({'error': 'Error fetching question details'}), 500

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
