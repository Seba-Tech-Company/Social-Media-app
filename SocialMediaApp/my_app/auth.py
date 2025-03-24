# Handles everything to do with the authorization of the users
from flask import Blueprint, render_template, url_for, request, redirect, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from my_app.db import get_db_connection
from flask_login import login_user, logout_user, login_required, current_user
from my_app.__init__ import User


# Create a blueprint which is to be registered in the init file
auth_blueprint = Blueprint('auth', __name__, url_prefix='/')


# Function to handle the signup of our users using the blueorint we just created
@auth_blueprint.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        phone = [request.form.get("phone")]

        if not username or not password:
            flash("All fields are required!", category='error')

        # Generate a password has for our users
        hashed_password = generate_password_hash(password)

        # Establish a connection
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed!", category='error')
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash("The email provided already exist!", category='error')

            cur.execute("INSERT INTO users (username, email, phone, password) VALUES (%s, %s, %s, %s) RETURNING user_id", (username, email, phone, hashed_password))
            session["user_id"] = cur.fetchone()[0]
            conn.commit()
            return redirect(url_for("user.get_feed"))
        finally:
            cur.close()
            conn.close()

    return render_template("Signup.html")



@auth_blueprint.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed!", category='error')
            return redirect(url_for("auth.signin"))

        try:
            cur = conn.cursor()
            cur.execute("SELECT user_id, username, password, email FROM users WHERE email = %s", (email,))
            user_data = cur.fetchone()

            if user_data and check_password_hash(user_data[2], password):  # user_data[2] = hashed password
                user = User(user_data[0], user_data[1], user_data[3])  # Convert tuple to User object
                login_user(user, remember=True)

                flash("Login successful!", category='success')
                return redirect(url_for("user.get_feed"))  # Redirect to feed

            flash("Invalid email or password!", category='error')

        finally:
            cur.close()
            conn.close()

    return render_template("Signin.html", user=current_user)



@auth_blueprint.route("/logout")
@login_required
def logout():
    logout_user()  # Logs out the current user
    flash("You have been logged out!", category="info")
    return redirect(url_for("auth.signin"))
