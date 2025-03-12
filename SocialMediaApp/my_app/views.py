import os
from flask import (
    Blueprint, request, jsonify, session, redirect, url_for, flash,
    current_app, render_template
)
from werkzeug.utils import secure_filename
from datetime import datetime
from my_app.db import mongo

# Define the Blueprint
user_blueprint = Blueprint("user", __name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"}

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_blueprint.route("/create_post", methods=["POST"])
def create_post():
    if "user_id" not in session:
        return redirect(url_for("auth.signin"))

    post_content = request.form.get("content", "").strip()
    media_file = request.files.get("media")
    media_filename = None

    # Handle media file upload
    if media_file and allowed_file(media_file.filename):
        filename = secure_filename(media_file.filename)
        media_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            media_file.save(media_path)
            media_filename = filename
        except Exception as e:
            flash(f"Error saving file: {e}", "danger")
            return redirect(url_for("user.feeds"))

    post_data = {
        "user_id": session["user_id"],
        "content": post_content,
        "media": media_filename,  # Store media filename
        "timestamp": datetime.utcnow(),
        "likes": 0,
        "comments": [],
    }

    try:
        mongo.db.posts.insert_one(post_data)
        flash("Post created successfully!", "success")
    except Exception as e:
        flash(f"Error creating post: {e}", "danger")

    return redirect(url_for("user.feeds"))

# Feeds route to display posts
@user_blueprint.route("/feeds")
def feeds():
    if "user_id" not in session:
        return redirect(url_for("auth.signin"))

    try:
        posts = list(mongo.db.posts.find().sort("timestamp", -1))  #
    except Exception as e:
        flash(f"Error fetching posts: {e}", "danger")
        posts = []

    return render_template("feeds.html", posts=posts)
