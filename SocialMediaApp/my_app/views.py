# Handles everything to do with how the user will be interacting with the application
from flask import Blueprint, render_template, url_for, request, jsonify, session, redirect
from my_app.db import get_db_connection, mongo

user_blueprint = Blueprint('user', __name__, url_prefix='/')


# Test PostgreSQL connection route
@user_blueprint.route("/test")
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

@user_blueprint.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("user.feeds"))
    return render_template("index.html")


@user_blueprint.route("/feeds")
def feeds():
    if "user_id" not in session:
        return redirect(url_for("auth.signin"))

    posts = list(mongo.db.posts.find().sort("_id", -1))  
    return render_template("feeds.html", posts=posts)