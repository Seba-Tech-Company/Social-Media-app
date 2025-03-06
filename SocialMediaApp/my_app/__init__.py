from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_pymongo import PyMongo
import psycopg2
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Load environment variables
load_dotenv()

# PostgreSQL Connection String
POSTGRES_URI = (
    f"dbname='{os.getenv('POSTGRES_DB')}' "
    f"user='{os.getenv('POSTGRES_USER')}' "
    f"password='{os.getenv('POSTGRES_PASSWORD')}' "
    f"host='{os.getenv('POSTGRES_HOST')}' "
    f"port='{os.getenv('POSTGRES_PORT')}'"
)

# MongoDB Setup
DB_NAME = "socialmedia"
MONGO_URI = f"mongodb://localhost:27017/{DB_NAME}"
mongo = PyMongo()

# Function to get PostgreSQL connection
def get_db_connection():
    try:
        conn = psycopg2.connect(POSTGRES_URI)
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# Flask App Factory
def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["MONGO_URI"] = MONGO_URI
    mongo.init_app(app)

    # Ensure MongoDB Indexing
    with app.app_context():
        mongo.db.posts.create_index([("created_at", -1)])

    # Test PostgreSQL connection route
    @app.route("/test")
    def test_postgres():
        # Establish connection to PostgreSQL
        conn = get_db_connection()
        
        if not conn:
            return "Error while connecting to PostgreSQL!", 500

        try:
            # Execute a sample query to ensure the connection works
            cur = conn.cursor()
            cur.execute("SELECT * FROM users LIMIT 1")  # Assuming a "users" table exists
            result = cur.fetchone()

            if result:
                return f"Connected to PostgreSQL! User data: {result}", 200
            else:
                return "No user data found in PostgreSQL!", 404

        except Exception as e:
            return f"Error while querying PostgreSQL: {e}", 500

        finally:
            cur.close()
            conn.close()

    @app.route("/")
    def home():
        if "user_id" in session:
            return redirect(url_for("feeds"))
        return render_template("index.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            if not username or not password:
                flash("All fields are required!", "danger")
                return redirect(url_for("signup"))

            hashed_password = generate_password_hash(password)
            conn = get_db_connection()
            if not conn:
                flash("Database connection failed!", "danger")
                return redirect(url_for("signup"))
            
            try:
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    flash("Username already exists!", "danger")
                    return redirect(url_for("signup"))

                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id", (username, hashed_password))
                session["user_id"] = cur.fetchone()[0]
                conn.commit()
                return redirect(url_for("feeds"))
            finally:
                cur.close()
                conn.close()

        return render_template("Signup.html")

    @app.route("/signin", methods=["GET", "POST"])
    def signin():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            conn = get_db_connection()
            if not conn:
                flash("Database connection failed!", "danger")
                return redirect(url_for("signin"))
            
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                user = cur.fetchone()
                
                if user and check_password_hash(user[1], password):
                    session["user_id"] = user[0]
                    return redirect(url_for("feeds"))

                flash("Invalid credentials!", "danger")
                return redirect(url_for("signin"))
            finally:
                cur.close()
                conn.close()

        return render_template("Signin.html")

    @app.route("/signout")
    def signout():
        session.pop("user_id", None)
        return redirect(url_for("home"))

    @app.route("/feeds")
    def feeds():
        if "user_id" not in session:
            return redirect(url_for("signin"))

        posts = list(mongo.db.posts.find().sort("_id", -1))  
        return render_template("feeds.html", posts=posts)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
