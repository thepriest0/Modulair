from app import app, db
from models import User

def check_database():
    with app.app_context():
        # Count users
        user_count = User.query.count()
        print(f"Number of users in database: {user_count}")
        
        # List all users
        users = User.query.all()
        for user in users:
            print(f"User: {user.username}, Email: {user.email}, Created at: {user.created_at}")

if __name__ == "__main__":
    check_database() 