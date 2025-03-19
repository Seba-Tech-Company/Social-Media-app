import os
from flask import Flask
from flask_login import LoginManager, UserMixin
from bson.objectid import ObjectId
from dotenv import load_dotenv
from my_app.db import mongo, get_db_connection, release_db_connection, MONGO_URI

# Load environment variables
load_dotenv()

# Flask App Factory
def create_app():
    app = Flask(__name__)

    # Configure Flask app
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["MONGO_URI"] = MONGO_URI
    app.config["UPLOAD_FOLDER"] = "static/uploads"  

    # Initialize MongoDB
    mongo.init_app(app)

    # Register blueprints
    from my_app.auth import auth_blueprint
    from my_app.views import user_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(user_blueprint)

    # Ensure MongoDB Indexing ✅ Fixed wrong field
    with app.app_context():
        mongo.db.posts.create_index([("timestamp", -1)])  

    # Set up Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.signin"
    login_manager.init_app(app)

    # User loader function for authentication
    @login_manager.user_loader
    def load_user(user_id):
        conn = get_db_connection()  # Get a PostgreSQL connection
        if not conn:
            return None

        try:
            cur = conn.cursor()
            cur.execute("SELECT id, username, email FROM users WHERE id = %s;", (user_id,))
            user_data = cur.fetchone()

            if user_data:
                class User(UserMixin):
                    def __init__(self, id, username, email):
                        self.id = id
                        self.username = username
                        self.email = email

                    def get_id(self):
                        return str(self.id)

                return User(*user_data)
            return None

        except Exception as e:
            print(f"Database Query Error (load_user): {e}")
            return None

        finally:
            conn.commit()
            release_db_connection(conn)  

    return app
