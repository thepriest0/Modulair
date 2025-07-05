from app import app, db
from sqlalchemy import text

def add_learning_style_columns():
    try:
        # Add preferred_learning_style to user table
        db.session.execute(text("""
            ALTER TABLE "user" 
            ADD COLUMN IF NOT EXISTS preferred_learning_style VARCHAR(50)
        """))
        
        # Add learning_style to course table with a default value
        db.session.execute(text("""
            ALTER TABLE course 
            ADD COLUMN IF NOT EXISTS learning_style VARCHAR(50) NOT NULL DEFAULT 'Visual'
        """))
        
        db.session.commit()
        print("Successfully added learning style columns")
        
    except Exception as e:
        print(f"Error adding columns: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    with app.app_context():
        add_learning_style_columns() 