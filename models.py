from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    
    # Profile fields
    bio = db.Column(db.Text)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    
    # Preferences
    email_notifications = db.Column(db.Boolean, default=True)
    course_reminders = db.Column(db.Boolean, default=True)
    marketing_emails = db.Column(db.Boolean, default=False)
    public_profile = db.Column(db.Boolean, default=False)
    
    # Learning preferences
    preferred_learning_style = db.Column(db.String(50))  # visual, auditory, kinesthetic, reading
    difficulty_preference = db.Column(db.String(20), default='intermediate')  # beginner, intermediate, advanced
    
    # Account info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(50), nullable=False)
    learning_style = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    outline = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    resources = db.Column(db.Text)  # JSON string of resource links
    youtube_video = db.Column(db.String(500))  # YouTube video URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON string
    lesson_dependency = db.Column(db.Integer, default=1)  # Which lesson must be completed before this quiz
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    current_lesson = db.Column(db.Integer, default=0)
    completion_percentage = db.Column(db.Integer, default=0)
    quiz_scores = db.Column(db.Text)  # JSON string to store quiz scores
    assignment_scores = db.Column(db.Text)  # JSON string to store assignment scores
    final_exam_score = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    assignment_type = db.Column(db.String(50), nullable=False)  # 'practical', 'project', 'coding', 'written'
    difficulty_level = db.Column(db.String(20), nullable=False)
    estimated_hours = db.Column(db.Integer, default=1)
    resources = db.Column(db.Text)  # JSON string for resources
    rubric = db.Column(db.Text)  # JSON string for grading rubric
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_text = db.Column(db.Text)
    file_urls = db.Column(db.Text)  # JSON string for file URLs
    status = db.Column(db.String(20), default='submitted')  # 'submitted', 'graded', 'feedback_given'
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    graded_at = db.Column(db.DateTime)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)  # JSON string
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)