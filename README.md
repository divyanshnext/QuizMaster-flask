
# Quiz Master - Online Quiz Management System

A comprehensive web-based quiz management system that allows administrators to create and manage quizzes while enabling users to take quizzes and track their performance.

## Features

### For Users
- User registration with detailed profile
- Access to available quizzes by subject and chapter
- Real-time quiz attempts with timer
- Performance tracking and analytics
- Detailed score history and summaries
- Interactive dashboard with performance charts

### For Administrators
- Secure admin dashboard
- Subject and chapter management
- Quiz creation and management
- Question bank management
- User performance analytics
- Search functionality for users, subjects, and quizzes
- Comprehensive reporting system

## Technologies Used
- Python 3.x
- Flask (Web Framework)
- SQLAlchemy (ORM)
- SQLite (Database)
- Chart.js (Data Visualization)
- Bootstrap 5 (UI Framework)
- Font Awesome (Icons)

## Database Schema

### User
- id (Primary Key)
- username (Unique)
- password
- full_name
- qualification
- dob

### Subject
- id (Primary Key)
- name (Unique)
- description

### Chapter
- id (Primary Key)
- subject_id (Foreign Key)
- name

### Quiz
- id (Primary Key)
- chapter_id (Foreign Key)
- date_of_quiz
- time_duration

### Question
- id (Primary Key)
- quiz_id (Foreign Key)
- question_statement
- option1
- option2
- option3
- option4
- correct_option

### Score
- id (Primary Key)
- quiz_id (Foreign Key)
- user_id (Foreign Key)
- total_scored

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd quizMaster
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

5. Run the application:
```bash
python app.py
```

6. Access the application:
- User Interface: http://localhost:5000
- Admin Interface: http://localhost:5000/admin_login  
  - Default Admin Credentials:
    - Username: `admin`
    - Password: `admin123`

## Project Structure

```
quizMaster/
├── app.py              # Main application file
├── models.py           # Database models
├── requirements.txt    # Project dependencies
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── instance/           # Database and instance-specific files
└── screenshots/        # Screenshots for README display
```

## Screenshots

### Home Page

![Home Page]![Screenshot 2025-05-26 232222](https://github.com/user-attachments/assets/23c56002-71c5-482f-bdad-d16782a33929)

## Security Features
- Separate user and admin authentication
- Session management
- Form validation
- Secure routing

## Future Improvements
1. Password hashing implementation
2. CSRF protection
3. Email verification
4. Password reset functionality
5. Advanced analytics
6. Mobile responsiveness improvements
7. API development for mobile apps
8. Real-time quiz monitoring
9. Bulk question import/export
10. Advanced search filters

## Contributing
Feel free to submit issues and enhancement requests!

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
