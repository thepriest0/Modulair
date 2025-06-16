import os
from dotenv import load_dotenv
import logging
import psycopg2
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection(url):
    try:
        # Use psycopg2 to test connection
        conn = psycopg2.connect(url)
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            logger.info(f"Successfully connected to database. Version: {version}")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def verify_tables():
    try:
        # Import app and models after successful connection test
        from app import app, db
        from models import User, Course, Lesson, Quiz, Progress, Assignment
        from models import AssignmentSubmission, QuizAttempt
        
        with app.app_context():
            logger.info("Verifying database tables...")
            
            # List of models to verify
            models = [User, Course, Lesson, Quiz, Progress, Assignment, 
                     AssignmentSubmission, QuizAttempt]
            
            success_count = 0
            for model in models:
                table_name = model.__tablename__
                try:
                    # Try to query the table
                    db.session.query(model).first()
                    logger.info(f"✓ Table '{table_name}' verified successfully")
                    success_count += 1
                except Exception as e:
                    logger.error(f"✗ Error verifying table '{table_name}': {str(e)}")
            
            if success_count == len(models):
                logger.info("All tables verified successfully!")
            else:
                logger.warning(f"Only {success_count} out of {len(models)} tables were verified successfully.")
            
            return success_count == len(models)
    except Exception as e:
        logger.error(f"Error during table verification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Get database URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        exit(1)
        
    logger.info("Testing database connection...")
    if not test_connection(database_url):
        logger.error("Failed to connect to database.")
        exit(1)
    
    logger.info("Verifying database tables...")
    if verify_tables():
        logger.info("Database setup verified successfully!")
    else:
        logger.error("Database verification failed.")
        exit(1) 