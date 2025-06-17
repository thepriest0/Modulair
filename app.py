import os
from dotenv import load_dotenv
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from ai_service import AIService
from flask_migrate import Migrate
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql.base import PGDialect

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Monkey patch the _get_server_version_info method for CockroachDB compatibility
def _get_server_version_info(self, connection):
    version = connection.scalar(text("SELECT version()"))
    if 'CockroachDB' in version:
        # Return a compatible PostgreSQL version
        return (9, 5, 0)
    return super(PGDialect, self)._get_server_version_info(connection)

PGDialect._get_server_version_info = _get_server_version_info

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
if os.environ.get("DATABASE_URL"):
    # Production database (PostgreSQL/CockroachDB)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
else:
    # Development database (SQLite)
    sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'modulair.db')
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize AI service
ai_service = AIService()

# Add custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python object"""
    if value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    return []

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models to ensure tables are created
    from models import User, Course, Lesson, Quiz, Progress, Assignment, AssignmentSubmission, QuizAttempt

    # Create tables if they don't exist
    db.create_all()

    # Handle database migrations
    import sqlalchemy as sa
    inspector = sa.inspect(db.engine)

    # Check and add missing columns
    user_columns = [column['name'] for column in inspector.get_columns('user')]
    print(f"User table columns: {user_columns}")

    if 'active' not in user_columns:
        print("ERROR: 'active' column not found in user table!")
        raise Exception("Database schema creation failed - missing 'active' column")

    # Check for youtube_video column in lesson table
    lesson_columns = [column['name'] for column in inspector.get_columns('lesson')]
    if 'youtube_video' not in lesson_columns:
        print("Adding youtube_video column to lesson table...")
        try:
            with db.engine.connect() as conn:
                conn.execute(sa.text("ALTER TABLE lesson ADD COLUMN youtube_video VARCHAR(500)"))
                conn.commit()
            print("Successfully added youtube_video column")
        except Exception as e:
            print(f"Note: Could not add youtube_video column: {e}")
            # Column might already exist or table needs recreation

    # Check for lesson_dependency column in quiz table
    quiz_columns = [column['name'] for column in inspector.get_columns('quiz')]
    if 'lesson_dependency' not in quiz_columns:
        print("Adding lesson_dependency column to quiz table...")
        try:
            with db.engine.connect() as conn:
                conn.execute(sa.text("ALTER TABLE quiz ADD COLUMN lesson_dependency INTEGER DEFAULT 1"))
                conn.commit()
            print("Successfully added lesson_dependency column")
        except Exception as e:
            print(f"Note: Could not add lesson_dependency column: {e}")
            # Column might already exist or table needs recreation

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        # Validation
        if not username or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        from models import User

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')

        # Create new user
        user = User()
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')

        from models import User

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            return redirect(url_for('index'))

        flash('Invalid username or password.', 'error')
        return render_template('auth/login.html')

    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Profile Management Routes
@app.route('/profile')
@login_required
def profile():
    """View user profile"""
    from models import Course, Progress
    
    # Get user's courses and progress
    courses = Course.query.filter_by(user_id=current_user.id).all()
    total_courses = len(courses)
    
    # Calculate completed courses
    completed_courses = 0
    total_progress = 0
    for course in courses:
        progress = Progress.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        if progress:
            total_progress += progress.completion_percentage
            if progress.completed_at:
                completed_courses += 1
    
    avg_progress = total_progress / total_courses if total_courses > 0 else 0
    
    return render_template('profile/profile.html', 
                         total_courses=total_courses,
                         completed_courses=completed_courses,
                         avg_progress=avg_progress)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile information"""
    if request.method == 'POST':
        # Update basic info
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.email = request.form.get('email', '').strip()
        current_user.bio = request.form.get('bio', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.location = request.form.get('location', '').strip()
        current_user.timezone = request.form.get('timezone', 'UTC')
        current_user.language = request.form.get('language', 'en')
        
        # Update learning preferences
        current_user.preferred_learning_style = request.form.get('preferred_learning_style')
        current_user.difficulty_preference = request.form.get('difficulty_preference', 'intermediate')
        
        # Check for email uniqueness if changed
        new_email = request.form.get('email')
        if new_email != current_user.email:
            from models import User
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                flash('Email address is already in use.', 'error')
                return render_template('profile/edit_profile.html')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
            logging.error(f"Profile update error: {e}")
    
    return render_template('profile/edit_profile.html')

@app.route('/account/settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    """Account settings and preferences"""
    if request.method == 'POST':
        # Update notification preferences
        current_user.email_notifications = bool(request.form.get('email_notifications'))
        current_user.course_reminders = bool(request.form.get('course_reminders'))
        current_user.marketing_emails = bool(request.form.get('marketing_emails'))
        current_user.public_profile = bool(request.form.get('public_profile'))
        
        try:
            db.session.commit()
            flash('Account settings updated successfully!', 'success')
            return redirect(url_for('account_settings'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating settings. Please try again.', 'error')
            logging.error(f"Settings update error: {e}")
    
    return render_template('profile/account_settings.html')

@app.route('/account/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('profile/change_password.html')
        
        # Validate new password
        if not new_password or len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return render_template('profile/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('profile/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error changing password. Please try again.', 'error')
            logging.error(f"Password change error: {e}")
    
    return render_template('profile/change_password.html')

@app.route('/account/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    """Delete user account"""
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_delete = request.form.get('confirm_delete')
        
        if not current_user.check_password(password):
            flash('Password is incorrect.', 'error')
            return render_template('profile/delete_account.html')
        
        if confirm_delete != 'DELETE':
            flash('Please type "DELETE" to confirm account deletion.', 'error')
            return render_template('profile/delete_account.html')
        
        try:
            # Delete user's data
            from models import Course, Progress, QuizAttempt, AssignmentSubmission
            
            # Delete all related data
            courses = Course.query.filter_by(user_id=current_user.id).all()
            for course in courses:
                # Delete course-related data
                Progress.query.filter_by(course_id=course.id).delete()
                QuizAttempt.query.filter(QuizAttempt.quiz_id.in_(
                    db.session.query(Quiz.id).filter_by(course_id=course.id)
                )).delete()
                AssignmentSubmission.query.filter(AssignmentSubmission.assignment_id.in_(
                    db.session.query(Assignment.id).filter_by(course_id=course.id)
                )).delete()
            
            # Delete courses
            Course.query.filter_by(user_id=current_user.id).delete()
            
            # Delete progress records
            Progress.query.filter_by(user_id=current_user.id).delete()
            
            # Delete user
            user_id = current_user.id
            db.session.delete(current_user)
            db.session.commit()
            
            logout_user()
            flash('Your account has been deleted successfully.', 'info')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error deleting account. Please try again.', 'error')
            logging.error(f"Account deletion error: {e}")
    
    return render_template('profile/delete_account.html')

@app.route('/')
def index():
    """Home page with dashboard"""
    if current_user.is_authenticated:
        recent_courses = Course.query.filter_by(user_id=current_user.id).order_by(Course.created_at.desc()).limit(3).all()
        return render_template('index.html', recent_courses=recent_courses)
    else:
        return render_template('landing.html')

@app.route('/create-course', methods=['GET', 'POST'])
@login_required
def create_course():
    """Course creation form and processing"""
    if request.method == 'POST':
        topic = request.form.get('topic')
        proficiency = request.form.get('proficiency')
        learning_style = request.form.get('learning_style')
        custom_topic = request.form.get('custom_topic')

        # Use custom topic if provided
        if custom_topic:
            topic = custom_topic

        if not topic or not proficiency or not learning_style:
            flash('Please fill in all required fields.', 'error')
            return render_template('create_course.html')

        # Redirect to progress page to show course generation progress
        session['course_params'] = {
            'topic': topic,
            'proficiency': proficiency,
            'learning_style': learning_style
        }
        return redirect(url_for('course_generation_progress'))

    return render_template('create_course.html')

@app.route('/course-generation-progress')
@login_required
def course_generation_progress():
    """Show course generation progress"""
    course_params = session.get('course_params')
    if not course_params:
        flash('No course generation in progress.', 'error')
        return redirect(url_for('create_course'))

    return render_template('course_generation_progress.html', params=course_params)

@app.route('/start-course-generation')
@login_required
def start_course_generation():
    """Start asynchronous course generation"""
    course_params = session.get('course_params')
    if not course_params:
        return jsonify({'error': 'No course parameters found'}), 400

    try:
        # Check A4F service health first
        if not ai_service.check_a4f_service_health():
            return jsonify({
                'error': 'A4F API service is currently unavailable. This is usually temporary due to high demand. Please wait 5-10 minutes and try again.'
            }), 503

        # Generate unique ID for this generation
        import uuid
        generation_id = str(uuid.uuid4())

        # Start background generation
        ai_service.start_course_generation(
            course_params['topic'], 
            course_params['proficiency'], 
            course_params['learning_style'],
            generation_id
        )

        # Store generation ID in session
        session['generation_id'] = generation_id

        return jsonify({
            'success': True, 
            'generation_id': generation_id,
            'status_url': url_for('check_generation_status')
        })

    except Exception as e:
        logging.error(f"Error starting course generation: {str(e)}")
        return jsonify({'error': f'Failed to start course generation: {str(e)}'}), 500

@app.route('/check-generation-status')
@login_required
def check_generation_status():
    """Check status of course generation"""
    generation_id = session.get('generation_id')
    if not generation_id:
        return jsonify({'error': 'No generation in progress'}), 400

    status = ai_service.get_generation_status(generation_id)

    if status['status'] == 'completed':
        # Generation is complete, prepare for preview
        course_data = ai_service.get_generation_result(generation_id)
        course_params = session.get('course_params')

        if course_data and course_params:
            try:
                # Store minimal data in session for preview
                session['course_preview'] = {
                    'topic': course_params['topic'],
                    'proficiency': course_params['proficiency'],
                    'learning_style': course_params['learning_style'],
                    'title': course_data.get('title', f"{course_params['topic']} Course"),
                    'description': course_data.get('description', ''),
                    'outline': course_data.get('outline', []),
                    'lesson_count': len(course_data.get('lessons', [])),
                    'quiz_count': len(course_data.get('quizzes', []))
                }

                # Store full course data temporarily in a file
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(course_data, temp_file)
                temp_file.close()
                session['course_data_file'] = temp_file.name

                # Clean up
                session.pop('course_params', None)
                session.pop('generation_id', None)
                ai_service.cleanup_generation(generation_id)

                status['redirect_url'] = url_for('preview_course')
                
                # Log successful completion
                logging.info(f"Course generation completed successfully for user {current_user.id}")
                
            except Exception as e:
                logging.error(f"Error preparing course preview: {str(e)}")
                status['status'] = 'error'
                status['message'] = 'Error preparing course preview. Please try again.'
        else:
            logging.error(f"Missing course data or params. course_data: {bool(course_data)}, course_params: {bool(course_params)}")
            status['status'] = 'error'
            status['message'] = 'Course generation completed but data is missing. Please try again.'

    return jsonify(status)

@app.route('/recover-courses')
@login_required
def recover_courses():
    """Help users recover from session issues by showing their existing courses"""
    courses = Course.query.filter_by(user_id=current_user.id).order_by(Course.id.desc()).all()
    
    if courses:
        flash('You have existing courses. You can continue with any of them below.', 'info')
        return redirect(url_for('my_courses'))
    else:
        flash('No existing courses found. Please create a new course.', 'info')
        return redirect(url_for('create_course'))

@app.route('/preview-course')
def preview_course():
    """Display AI-generated course preview"""
    course_preview = session.get('course_preview')
    course_data_file = session.get('course_data_file')

    if not course_preview or not course_data_file:
        # Add debugging information
        logging.warning(f"Preview course accessed without session data. course_preview: {bool(course_preview)}, course_data_file: {bool(course_data_file)}")
        
        # Check if there are any recent courses for this user
        if current_user.is_authenticated:
            recent_course = Course.query.filter_by(user_id=current_user.id).order_by(Course.id.desc()).first()
            if recent_course:
                flash('No course preview available. You can continue with your existing courses or create a new one.', 'error')
                return redirect(url_for('my_courses'))
        
        flash('No course preview available. Please create a course first.', 'error')
        return redirect(url_for('create_course'))

    # Load full course data from file
    try:
        with open(course_data_file, 'r') as f:
            course_data = json.load(f)

        # Combine preview data with full course data
        full_course = course_preview.copy()
        full_course['course_data'] = course_data

        return render_template('preview_course.html', course=full_course)
    except Exception as e:
        logging.error(f"Error loading course data: {str(e)}")
        flash('Error loading course preview. Please create a course again.', 'error')
        return redirect(url_for('create_course'))

@app.route('/start-course', methods=['POST'])
@login_required
def start_course():
    """Initialize the course and begin progress tracking"""
    course_preview = session.get('course_preview')
    course_data_file = session.get('course_data_file')

    if not course_preview or not course_data_file:
        logging.warning(f"Start course accessed without session data. course_preview: {bool(course_preview)}, course_data_file: {bool(course_data_file)}")
        flash('No course preview available. Please create a course first.', 'error')
        return redirect(url_for('create_course'))

    try:
        # Load full course data from file
        with open(course_data_file, 'r') as f:
            course_data = json.load(f)

        # Create course record
        course = Course()
        course.user_id = current_user.id
        course.title = course_data['title']
        course.topic = course_preview['topic']
        course.proficiency = course_preview['proficiency']
        course.learning_style = course_preview['learning_style']
        course.description = course_data['description']
        course.outline = json.dumps(course_data['outline'])
        db.session.add(course)
        db.session.flush()  # Get the course ID

        # Create lessons
        lessons_data = course_data['lessons']
        for i, lesson_data in enumerate(lessons_data):
            lesson = Lesson()
            lesson.course_id = course.id
            lesson.title = lesson_data['title']
            lesson.content = lesson_data['content']
            lesson.order_index = i
            lesson.resources = json.dumps(lesson_data.get('resources', []))
            lesson.youtube_video = lesson_data.get('youtube_video', '')
            db.session.add(lesson)

        db.session.flush()  # Get lesson IDs

        # Create quizzes with lesson dependencies
        quizzes_data = course_data['quizzes']
        lessons = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.order_index).all()

        for quiz_data in quizzes_data:
            quiz = Quiz()
            quiz.course_id = course.id
            quiz.title = quiz_data['title']
            quiz.questions = json.dumps(quiz_data['questions'])
            quiz.lesson_dependency = quiz_data.get('lesson_dependency', 1)
            # Link quiz to specific lesson if dependency exists
            if quiz.lesson_dependency <= len(lessons):
                quiz.lesson_id = lessons[quiz.lesson_dependency - 1].id
            db.session.add(quiz)

        # Create assignments if they exist
        assignments_data = course_data.get('assignments', [])
        for assignment_data in assignments_data:
            assignment = Assignment()
            assignment.course_id = course.id
            assignment.title = assignment_data['title']
            assignment.description = assignment_data['description']
            assignment.instructions = assignment_data['instructions']
            assignment.assignment_type = assignment_data['type']
            assignment.difficulty_level = assignment_data['difficulty']
            assignment.estimated_hours = assignment_data['estimated_hours']
            assignment.resources = json.dumps(assignment_data.get('resources', []))
            db.session.add(assignment)

        # Create final exam if it exists
        final_exam_data = course_data.get('final_exam')
        if final_exam_data:
            final_quiz = Quiz()
            final_quiz.course_id = course.id
            final_quiz.lesson_id = None
            final_quiz.title = final_exam_data['title']
            final_quiz.questions = json.dumps(final_exam_data['questions'])
            db.session.add(final_quiz)

        # Initialize progress
        progress = Progress()
        progress.user_id = current_user.id
        progress.course_id = course.id
        progress.current_lesson = 0
        progress.completion_percentage = 0
        db.session.add(progress)

        db.session.commit()

        # Clean up temp file and session data
        import os
        if os.path.exists(course_data_file):
            os.unlink(course_data_file)
        session.pop('course_preview', None)
        session.pop('course_data_file', None)

        flash('Course started successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error starting course: {str(e)}")
        flash('Error starting course. Please try again.', 'error')
        return redirect(url_for('preview_course'))

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    """Display course content, lessons, and progress"""

    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))

    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    assignments = Assignment.query.filter_by(course_id=course_id).all()

    if not progress:
        # Create initial progress if it doesn't exist
        progress = Progress()
        progress.user_id = current_user.id
        progress.course_id = course_id
        progress.current_lesson = 0
        progress.completion_percentage = 0
        db.session.add(progress)
        db.session.commit()

    current_lesson = None
    if lessons and progress.current_lesson < len(lessons):
        current_lesson = lessons[progress.current_lesson]

    return render_template('course.html', 
                         course=course, 
                         lessons=lessons, 
                         progress=progress,
                         current_lesson=current_lesson,
                         quizzes=quizzes,
                         assignments=assignments)

@app.route('/course/<int:course_id>/lesson/<int:lesson_index>')
@login_required
def course_lesson(course_id, lesson_index):
    """Navigate directly to a specific lesson if unlocked"""
    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))
    
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    
    if not progress:
        # Create initial progress if it doesn't exist
        progress = Progress()
        progress.user_id = current_user.id
        progress.course_id = course_id
        progress.current_lesson = 0
        progress.completion_percentage = 0
        db.session.add(progress)
        db.session.commit()
    
    # Check if lesson is unlocked (can access current lesson or any previous lesson)
    if lesson_index > progress.current_lesson:
        flash('This lesson is locked. Complete previous lessons first.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    # Validate lesson index
    if lesson_index < 0 or lesson_index >= len(lessons):
        flash('Lesson not found.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    # Update progress to this lesson if user is navigating to a previous lesson
    # This allows reviewing previous content
    temp_current_lesson = progress.current_lesson
    progress.current_lesson = lesson_index
    db.session.commit()
    
    # Get course data for display
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    current_lesson = lessons[lesson_index]
    
    # Restore original lesson progress if user was reviewing a previous lesson
    if lesson_index < temp_current_lesson:
        progress.current_lesson = temp_current_lesson
        db.session.commit()
    
    return render_template('course.html', 
                         course=course, 
                         lessons=lessons, 
                         current_lesson=current_lesson,
                         progress=progress,
                         quizzes=quizzes,
                         assignments=assignments)

@app.route('/next-lesson/<int:course_id>')
@login_required
def next_lesson(course_id):
    """Move to the next lesson with quiz validation"""
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not progress:
        flash('Progress not found.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
    current_lesson = lessons[progress.current_lesson] if progress.current_lesson < len(lessons) else None

    if not current_lesson:
        flash('No more lessons available.', 'info')
        return redirect(url_for('course_detail', course_id=course_id))

    # Check if there are any quizzes that require the current lesson
    current_lesson_quizzes = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.lesson_dependency == progress.current_lesson + 1,  # +1 because lesson_dependency is 1-based
        ~Quiz.title.contains('Final')  # Exclude final exams
    ).all()
    
    # If there are quizzes for this lesson, redirect to the first unpassed quiz
    for quiz in current_lesson_quizzes:
        passed_attempt = QuizAttempt.query.filter_by(
            quiz_id=quiz.id,
            user_id=current_user.id,
            passed=True
        ).first()
        
        if not passed_attempt:
            # Redirect to quiz instead of showing a warning
            return redirect(url_for('quiz', quiz_id=quiz.id))

    # Move to next lesson only if all quizzes are passed
    if progress.current_lesson < len(lessons) - 1:
        progress.current_lesson += 1
        progress.completion_percentage = int((progress.current_lesson + 1) / len(lessons) * 100)
        db.session.commit()

        if progress.completion_percentage >= 100:
            flash('Congratulations! You have completed all lessons! Now take the final exam.', 'success')
    else:
        flash('You have completed all lessons! Take the final exam to get your certificate.', 'info')

    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/quiz/<int:quiz_id>')
@login_required
def quiz(quiz_id):
    """Display specific quiz"""
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz_obj.course_id, user_id=current_user.id).first()

    if not course:
        flash('Quiz not found.', 'error')
        return redirect(url_for('index'))

    # Prevent direct access to final exams through quiz route
    if 'Final' in quiz_obj.title:
        flash('Please access the final exam through the course page after completing all lessons.', 'warning')
        return redirect(url_for('course_detail', course_id=course.id))

    # Check if user has started the course
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not progress:
        flash('You must start the course before taking quizzes.', 'error')
        return redirect(url_for('course_detail', course_id=course.id))

    # Check lesson dependency - user must be at or have completed the required lesson
    if quiz_obj.lesson_dependency:
        # Subtract 1 because lesson_dependency is 1-based but current_lesson is 0-based
        required_lesson = quiz_obj.lesson_dependency - 1
        if progress.current_lesson < required_lesson:
            flash(f'You must complete lesson {quiz_obj.lesson_dependency} before taking this quiz.', 'warning')
            return redirect(url_for('course_detail', course_id=course.id))

    # Check if user has already passed this quiz
    attempt = QuizAttempt.query.filter_by(
        quiz_id=quiz_id,
        user_id=current_user.id,
        passed=True
    ).first()

    if attempt:
        flash('You have already passed this quiz.', 'info')
        return redirect(url_for('course_detail', course_id=course.id))

    # Redirect to first question for new quiz system
    return redirect(url_for('quiz_question', quiz_id=quiz_id, question_num=1))

@app.route('/quiz/<int:quiz_id>/question/<int:question_num>')
@login_required
def quiz_question(quiz_id, question_num):
    """Display a single quiz question"""
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz_obj.course_id, user_id=current_user.id).first()

    if not course:
        flash('Quiz not found.', 'error')
        return redirect(url_for('index'))

    questions = json.loads(quiz_obj.questions)

    if question_num < 1 or question_num > len(questions):
        return redirect(url_for('quiz', quiz_id=quiz_id))

    question = questions[question_num - 1]
    question['number'] = question_num

    # Get stored answers from session
    session_key = f'quiz_{quiz_id}_answers'
    stored_answers = session.get(session_key, {})

    return render_template('quiz_question.html', 
                         course=course, 
                         quiz=quiz_obj, 
                         question=question,
                         question_num=question_num,
                         total_questions=len(questions),
                         stored_answer=stored_answers.get(str(question_num - 1)))

@app.route('/quiz/<int:quiz_id>/answer/<int:question_num>', methods=['POST'])
@login_required
def submit_quiz_answer(quiz_id, question_num):
    """Submit answer for a single question"""
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz_obj.course_id, user_id=current_user.id).first()

    if not course:
        flash('Quiz not found.', 'error')
        return redirect(url_for('index'))

    questions = json.loads(quiz_obj.questions)
    user_answer = request.form.get('answer')

    # Store answer in session
    session_key = f'quiz_{quiz_id}_answers'
    stored_answers = session.get(session_key, {})
    stored_answers[str(question_num - 1)] = user_answer
    session[session_key] = stored_answers

    # Navigate to next question or submit quiz
    if question_num < len(questions):
        return redirect(url_for('quiz_question', quiz_id=quiz_id, question_num=question_num + 1))
    else:
        return redirect(url_for('submit_quiz', quiz_id=quiz_id))

@app.route('/submit-quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def submit_quiz(quiz_id):
    """Handle final quiz submission and scoring"""
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz_obj.course_id, user_id=current_user.id).first()

    if not course:
        flash('Quiz not found.', 'error')
        return redirect(url_for('index'))

    questions = json.loads(quiz_obj.questions)
    session_key = f'quiz_{quiz_id}_answers'
    user_answers = session.get(session_key, {})

    if request.method == 'GET':
        # Show review page
        return render_template('quiz_review.html', 
                             course=course, 
                             quiz=quiz_obj, 
                             questions=questions,
                             user_answers=user_answers)

    # Calculate score using batch AI grading to prevent rate limiting
    from ai_service import AIService
    ai_service = AIService()
    
    # Prepare batch data for grading
    questions_data = []
    for i, question in enumerate(questions):
        user_answer = user_answers.get(str(i))
        correct_answer = (question.get('correct_answer') or 
                         question.get('answer') or 
                         question.get('sample_answer'))
        if not correct_answer:
            logging.warning(f"No correct answer found for question {i}: {question}")
            continue
            
        questions_data.append({
            'question_text': question.get('question', ''),
            'question_type': question.get('type', 'multiple_choice'),
            'correct_answer': correct_answer,
            'user_answer': user_answer or ""
        })

    # Get lesson context for better grading
    lesson_context = course.topic if course else ""
    
    # Use batch grading to reduce API calls
    if len(questions_data) > 10:
        # For large exams (>10 questions), use batch grading in chunks
        batch_results = []
        chunk_size = 8  # Process 8 questions at a time
        for i in range(0, len(questions_data), chunk_size):
            chunk = questions_data[i:i+chunk_size]
            chunk_results = ai_service.grade_answers_batch(chunk, lesson_context)
            batch_results.extend(chunk_results)
    else:
        # For smaller quizzes, process all at once
        batch_results = ai_service.grade_answers_batch(questions_data, lesson_context)
    
    # Calculate final scores
    score = 0.0
    total_questions = len(questions_data)
    detailed_results = []
    all_correct = True
    for i, (question, grading_result) in enumerate(zip(questions[:len(batch_results)], batch_results)):
        user_answer = user_answers.get(str(i))
        score += grading_result['score']
        detailed_results.append({
            'question_num': i + 1,
            'question': question.get('question', ''),
            'user_answer': user_answer,
            'score': grading_result['score'],
            'feedback': grading_result['feedback'],
            'is_correct': grading_result['is_correct']
        })
        # Accept both correct and almost correct (score >= 0.5) as correct
        if not grading_result['is_correct'] and grading_result['score'] < 0.5:
            all_correct = False

    percentage = (score / total_questions) * 100

    # Different passing requirements for different quiz types
    if 'Final' in quiz_obj.title or 'Exam' in quiz_obj.title:
        passing_score = 80  # 80% for final exam to get certificate
        passed = percentage >= passing_score
    else:
        # For regular quizzes: must get all questions correct
        passed = all_correct

    # Get attempt number
    previous_attempts = QuizAttempt.query.filter_by(
        quiz_id=quiz_id,
        user_id=current_user.id
    ).count()

    # Record quiz attempt
    attempt = QuizAttempt()
    attempt.quiz_id = quiz_id
    attempt.user_id = current_user.id
    attempt.answers = json.dumps(user_answers)
    attempt.score = score
    attempt.total_questions = total_questions
    attempt.percentage = percentage
    attempt.passed = passed
    attempt.attempt_number = previous_attempts + 1
    db.session.add(attempt)
    db.session.commit()

    # Clear session data
    session.pop(session_key, None)

    if passed:
        if 'Final' in quiz_obj.title or 'Exam' in quiz_obj.title:
            flash(f'Congratulations! You passed with {percentage:.1f}%', 'success')
            return redirect(url_for('course_detail', course_id=course.id))
        else:
            flash(f'Congratulations! You got all questions correct and passed!', 'success')
            # After passing a regular quiz, redirect to next lesson automatically
            return redirect(url_for('next_lesson', course_id=course.id))
    else:
        if 'Final' in quiz_obj.title or 'Exam' in quiz_obj.title:
            flash(f'You scored {percentage:.1f}%. You need 80% to pass. Please try again.', 'error')
        else:
            flash(f'You must get all questions correct to pass. Please try again.', 'error')
        return redirect(url_for('quiz', quiz_id=quiz_id))

@app.route('/final-exam/<int:course_id>')
@login_required
def final_exam(course_id):
    """Display final exam for the course"""
    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))

    # Check if user has completed all lessons
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not progress or progress.completion_percentage < 100:
        flash('You must complete all lessons before taking the final exam.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))

    # Check if all lesson quizzes are passed
    lesson_quizzes = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.title.notlike('%Final%'),
        Quiz.lesson_dependency.isnot(None)
    ).all()
    
    for lesson_quiz in lesson_quizzes:
        passed_attempt = QuizAttempt.query.filter_by(
            quiz_id=lesson_quiz.id,
            user_id=current_user.id,
            passed=True
        ).first()

        if not passed_attempt:
            flash(f'You must pass "{lesson_quiz.title}" before taking the final exam.', 'warning')
            return redirect(url_for('quiz', quiz_id=lesson_quiz.id))

    # Find final exam (quiz with "Final" in title)
    final_quiz = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.title.contains('Final')
    ).first()

    if not final_quiz:
        flash('Final exam not available.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    # Check if user has already passed the final exam
    passed_attempt = QuizAttempt.query.filter_by(
        quiz_id=final_quiz.id,
        user_id=current_user.id,
        passed=True
    ).first()

    if passed_attempt:
        flash('You have already passed the final exam!', 'success')
        return redirect(url_for('certificate', course_id=course_id))

    # Redirect to first question of final exam
    return redirect(url_for('final_exam_question', course_id=course_id, question_num=1))

@app.route('/final-exam/<int:course_id>/question/<int:question_num>')
@login_required
def final_exam_question(course_id, question_num):
    """Display a single final exam question"""
    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))

    # Find final exam
    final_quiz = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.title.contains('Final')
    ).first()

    if not final_quiz:
        flash('Final exam not found.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    questions = json.loads(final_quiz.questions)

    if question_num < 1 or question_num > len(questions):
        return redirect(url_for('final_exam', course_id=course_id))

    question = questions[question_num - 1]
    question['number'] = question_num

    # Get stored answers from session
    session_key = f'final_exam_{course_id}_answers'
    stored_answers = session.get(session_key, {})

    return render_template('final_exam_question.html', 
                         course=course, 
                         quiz=final_quiz, 
                         question=question,
                         question_num=question_num,
                         total_questions=len(questions),
                         stored_answer=stored_answers.get(str(question_num - 1)))

@app.route('/final-exam/<int:course_id>/answer/<int:question_num>', methods=['POST'])
@login_required
def submit_final_exam_answer(course_id, question_num):
    """Submit answer for a single final exam question"""
    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))

    # Find final exam
    final_quiz = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.title.contains('Final')
    ).first()

    if not final_quiz:
        flash('Final exam not found.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    questions = json.loads(final_quiz.questions)
    user_answer = request.form.get('answer')

    # Store answer in session
    session_key = f'final_exam_{course_id}_answers'
    stored_answers = session.get(session_key, {})
    stored_answers[str(question_num - 1)] = user_answer
    session[session_key] = stored_answers

    # Navigate to next question or submit final exam
    if question_num < len(questions):
        return redirect(url_for('final_exam_question', course_id=course_id, question_num=question_num + 1))
    else:
        return redirect(url_for('submit_final_exam', course_id=course_id))

@app.route('/submit-final-exam/<int:course_id>', methods=['GET', 'POST'])
@login_required
def submit_final_exam(course_id):
    """Handle final exam submissions"""
    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))

    # Find final exam
    final_quiz = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.title.contains('Final')
    ).first()

    if not final_quiz:
        flash('Final exam not found.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    questions = json.loads(final_quiz.questions)
    session_key = f'final_exam_{course_id}_answers'
    user_answers = session.get(session_key, {})

    if request.method == 'GET':
        # Show review page
        return render_template('final_exam_review.html', 
                             course=course, 
                             quiz=final_quiz, 
                             questions=questions,
                             user_answers=user_answers)

    # Calculate score using batch AI grading to prevent rate limiting
    from ai_service import AIService
    ai_service = AIService()
    
    # Prepare batch data for grading
    questions_data = []
    for i, question in enumerate(questions):
        user_answer = user_answers.get(str(i))
        correct_answer = (question.get('correct_answer') or 
                         question.get('answer') or 
                         question.get('sample_answer'))
        if not correct_answer:
            logging.warning(f"No correct answer found for final exam question {i}: {question}")
            continue
            
        questions_data.append({
            'question_text': question.get('question', ''),
            'question_type': question.get('type', 'multiple_choice'),
            'correct_answer': correct_answer,
            'user_answer': user_answer or ""
        })

    # Get lesson context for better grading
    lesson_context = f"{course.topic} - Final Exam" if course else "Final Exam"
    
    # Use batch grading in chunks for final exams (usually 18-20 questions)
    batch_results = []
    chunk_size = 6  # Smaller chunks for final exam to ensure quality
    for i in range(0, len(questions_data), chunk_size):
        chunk = questions_data[i:i+chunk_size]
        chunk_results = ai_service.grade_answers_batch(chunk, lesson_context)
        batch_results.extend(chunk_results)
    
    # Calculate final scores
    score = 0.0
    total_questions = len(questions_data)
    detailed_results = []
    
    for i, (question, grading_result) in enumerate(zip(questions[:len(batch_results)], batch_results)):
        user_answer = user_answers.get(str(i))
        score += grading_result['score']
        detailed_results.append({
            'question_num': i + 1,
            'question': question.get('question', ''),
            'user_answer': user_answer,
            'score': grading_result['score'],
            'feedback': grading_result['feedback'],
            'is_correct': grading_result['is_correct']
        })

    percentage = (score / total_questions) * 100
    passing_score = 80  # 80% to pass final exam
    passed = percentage >= passing_score

    # Get attempt number
    previous_attempts = QuizAttempt.query.filter_by(
        quiz_id=final_quiz.id,
        user_id=current_user.id
    ).count()

    # Record final exam attempt
    attempt = QuizAttempt()
    attempt.quiz_id = final_quiz.id
    attempt.user_id = current_user.id
    attempt.answers = json.dumps(user_answers)
    attempt.score = score
    attempt.total_questions = total_questions
    attempt.percentage = percentage
    attempt.passed = passed
    attempt.attempt_number = previous_attempts + 1
    db.session.add(attempt)

    # Clear session data
    session.pop(session_key, None)

    # Update progress if passed
    if passed:
        progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
        if progress:
            progress.final_exam_score = int(percentage)
            progress.completed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Congratulations! You passed the final exam with {percentage:.1f}%!', 'success')
        return redirect(url_for('certificate', course_id=course_id))
    else:
        db.session.commit()
        flash(f'You scored {percentage:.1f}%. You need 80% to pass. Please study and try again.', 'error')
        return redirect(url_for('final_exam', course_id=course_id))

@app.route('/certificate/<int:course_id>')
@login_required
def certificate(course_id):
    """Generate and display certificate upon completion"""
    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()

    if not course or not progress:
        flash('Certificate not available. Course not found.', 'error')
        return redirect(url_for('index'))

    # Check if final exam was passed
    final_quiz = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.title.contains('Final')
    ).first()

    if final_quiz:
        passed_final = QuizAttempt.query.filter_by(
            quiz_id=final_quiz.id,
            user_id=current_user.id,
            passed=True
        ).first()

        if not passed_final:
            flash('Certificate not available. Please pass the final exam first.', 'error')
            return redirect(url_for('final_exam', course_id=course_id))

    # Get lesson count and final exam score
    lessons_count = Lesson.query.filter_by(course_id=course_id).count()
    final_exam_score = progress.final_exam_score or 0

    completion_date = progress.completed_at or datetime.utcnow()
    return render_template('certificate.html', 
                         course=course, 
                         user=current_user,
                         completion_date=completion_date,
                         final_exam_score=final_exam_score,
                         lessons_count=lessons_count)

@app.route('/my-courses')
@login_required
def my_courses():
    """Display all user's courses"""
    courses = Course.query.filter_by(user_id=current_user.id).order_by(Course.created_at.desc()).all()

    # Get progress for each course
    courses_with_progress = []
    for course in courses:
        progress = Progress.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        courses_with_progress.append({
            'course': course,
            'progress': progress
        })

    return render_template('my_courses.html', courses_with_progress=courses_with_progress)

# Assignment routes
@app.route('/course/<int:course_id>/assignments')
@login_required
def course_assignments(course_id):
    """Display assignments for a course"""
    course = Course.query.filter_by(id=course_id, user_id=current_user.id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('index'))

    assignments = Assignment.query.filter_by(course_id=course_id).all()

    # Get submission status for each assignment
    assignments_with_status = []
    for assignment in assignments:
        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment.id,
            user_id=current_user.id
        ).first()
        assignments_with_status.append({
            'assignment': assignment,
            'submission': submission
        })

    return render_template('assignments.html', course=course, assignments_with_status=assignments_with_status)

@app.route('/assignment/<int:assignment_id>')
@login_required
def assignment_detail(assignment_id):
    """Display assignment details and submission form"""
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.filter_by(id=assignment.course_id, user_id=current_user.id).first()

    if not course:
        flash('Assignment not found.', 'error')
        return redirect(url_for('index'))

    # Check if user has already submitted
    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        user_id=current_user.id
    ).first()

    return render_template('assignment_detail.html', assignment=assignment, course=course, submission=submission)

@app.route('/assignment/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    """Handle assignment submissions"""
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.filter_by(id=assignment.course_id, user_id=current_user.id).first()

    if not course:
        flash('Assignment not found.', 'error')
        return redirect(url_for('index'))

    submission_text = request.form.get('submission_text')

    if not submission_text:
        flash('Please provide your submission.', 'error')
        return redirect(url_for('assignment_detail', assignment_id=assignment_id))

    # Check if already submitted
    existing_submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        user_id=current_user.id
    ).first()

    if existing_submission:
        # Update existing submission
        existing_submission.submission_text = submission_text
        existing_submission.status = 'submitted'
        existing_submission.submitted_at = datetime.utcnow()
    else:
        # Create new submission
        submission = AssignmentSubmission()
        submission.assignment_id = assignment_id
        submission.user_id = current_user.id
        submission.submission_text = submission_text
        submission.status = 'submitted'
        db.session.add(submission)

    db.session.commit()
    flash('Assignment submitted successfully!', 'success')
    return redirect(url_for('course_assignments', course_id=course.id))

@app.route('/debug-session')
@login_required
def debug_session():
    """Debug route to check session state (development only)"""
    session_data = {
        'course_params': session.get('course_params'),
        'generation_id': session.get('generation_id'),
        'course_preview': session.get('course_preview'),
        'course_data_file': session.get('course_data_file'),
        'user_id': current_user.id if current_user.is_authenticated else None
    }
    
    # Also check for existing courses
    if current_user.is_authenticated:
        courses = Course.query.filter_by(user_id=current_user.id).all()
        session_data['existing_courses'] = [{'id': c.id, 'title': c.title} for c in courses]
    
    return jsonify(session_data)

@app.errorhandler(404)
def not_found(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html'), 500