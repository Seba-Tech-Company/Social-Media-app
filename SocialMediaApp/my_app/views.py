import os
from flask import (
    Blueprint, request, jsonify, session, redirect, url_for, flash,
    current_app, render_template
)
from werkzeug.utils import secure_filename
from datetime import datetime
from my_app.db import mongo
from my_app.db import get_db_connection, release_db_connection
from psycopg2.extras import RealDictCursor
from flask_login import current_user, login_required
from bson.objectid import ObjectId


# Define the Blueprint
user_blueprint = Blueprint("user", __name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join("my_app/static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"}

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@user_blueprint.route("/")
def home():
    return render_template("index.html")



@user_blueprint.route('/feed')
@login_required
def get_feed():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        user_id = current_user.get_id()
        username = current_user.username

        posts = list(mongo.db.posts.find().sort("timestamp", -1))

        if not posts:  
            return jsonify({"error": "No posts found"}), 404

        for post in posts:
            # Ensure _id is a string for processing
            post["_id"] = str(post["_id"])  # Convert ObjectId to string

            # Get like count from PostgreSQL
            cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post["_id"],))
            post["likes"] = cursor.fetchone()["count"]

            # Check if the current user liked the post
            cursor.execute("SELECT like_id FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post["_id"]))
            post["liked_by_user"] = cursor.fetchone() is not None

            # Process comments
            post["comments"] = [
                {
                    "comment_id": str(comment["comment_id"]),  # Convert _id to string
                    "user_id": comment.get("user_id"),
                    "username": comment.get("username"),
                    "content": comment.get("content"),
                    "timestamp": comment.get("timestamp"),
                    "likes": comment.get("likes", 0),
                    "replies": [
                        {
                            "reply_id": str(reply["_id"]),  # Convert reply _id to string
                            "user_id": reply.get("user_id"),
                            "username": reply.get("username"),
                            "content": reply.get("content"),
                            "likes": reply.get("likes", 0),
                            "timestamp": reply.get("timestamp")
                        }
                        for reply in comment.get("replies", [])
                    ]
                }
                for comment in post.get("comments", [])
            ]


            # Get the media file path
            if post.get("media"):
                post["media_url"] = url_for('static', filename='uploads/' + os.path.basename(post["media"]))
            else:
                post["media_url"] = None

        return render_template("feeds.html", posts=posts, user_id=user_id, username=username)

    except Exception as e:
        print("Error in get_feed:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)

            


@user_blueprint.route('/reply', methods=['POST'])
@login_required
def create_reply():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        print(data)
        user_id = data.get("user_id")
        post_id = data.get("post_id")
        parent_comment_id = data.get("parent_comment_id")  # Required for replies
        content = data.get("content")

        if not user_id or not post_id or not parent_comment_id or not content:
            return jsonify({"error": "Missing required fields"}), 400

        # Get username from PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
        user_result = cursor.fetchone()
        cursor.close()
        conn.close()

        username = user_result["username"] if user_result else "Unknown"

        reply_data = {
            "_id": ObjectId(),  # Assign a unique ID to the reply
            "user_id": user_id,
            "username": username,
            "content": content,
            "timestamp": datetime.utcnow(),
            "likes": 0  
        }

        # Update the correct comment inside MongoDB
        result = mongo.db.posts.update_one(
            {"_id": ObjectId(post_id), "comments.comment_id": parent_comment_id},
            {"$push": {"comments.$.replies": reply_data}}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Parent comment not found"}), 404

        return jsonify({"message": "Reply added!", "reply": reply_data}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()  
        if conn:
            release_db_connection(conn)







@user_blueprint.route('/create_post', methods=['POST'])
@login_required 
def create_post():
    conn = None
    cursor = None

    try:
        user_id = current_user.get_id()  # Get user ID from Flask-Login

        # Fetch username from PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
        user_result = cursor.fetchone()

        username = user_result["username"] if user_result else "Unknown"

        # Get post data
        content = request.form.get("content")
        media_file = request.files.get("media")

        media_path = None

        if media_file and allowed_file(media_file.filename):
            filename = secure_filename(media_file.filename)  # Make it safe
            media_path = os.path.join("static", "uploads", filename)  # Define path
            media_file.save(os.path.join(UPLOAD_FOLDER, filename))

        if not content:
            return jsonify({"error": "Content is required"}), 400

        # Insert post into MongoDB
        post_data = {
            "user_id": user_id,
            "username": username,
            "content": content,
            "media": media_path,
            "timestamp": datetime.utcnow(),
            "likes": 0,
            "comments": []
        }
        mongo.db.posts.insert_one(post_data)

        return jsonify({"message": "Post created successfully", "post": post_data}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()  
        if conn:
            release_db_connection(conn)  # Make sure the connection is released!



@user_blueprint.route('/like', methods=['POST'])
@login_required
def like_post():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        post_id = data.get("post_id")

        print(f"user: {user_id}, post: {post_id}")

        if not user_id or not post_id:
            return jsonify({"error": "Missing user_id or post_id"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if user already liked the comment
        cursor.execute("SELECT 1 FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
        existing_like = cursor.fetchone()

        if existing_like:
            # Unlike the post
            cursor.execute("DELETE FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
            conn.commit()
            message = "Comment unliked"
        else:
            # Like the post
            cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (%s, %s)", (user_id, post_id))
            conn.commit()
            message = "Comment liked"

        # Get updated like count
        cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id,))
        like_count = cursor.fetchone()["count"]

        return jsonify({"message": message, "likes": like_count}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()  
        if conn:
            release_db_connection(conn)  # Make sure the connection is released!



@user_blueprint.route('/like_comment', methods=['POST'])
@login_required
def like_comment():
    conn = None
    cursor = None
    try:
        data = request.json
        user_id = current_user.get_id()
        comment_id = data.get("comment_id")

        print("Received data:", data)  # Debugging

        if not comment_id or not user_id:
            return jsonify({"error": "Missing user_id or comment_id"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if user already liked the comment
        cursor.execute("SELECT 1 FROM comment_likes WHERE user_id = %s AND comment_id = %s", (user_id, comment_id))
        existing_like = cursor.fetchone()

        if existing_like:
            print("Exists")
            # Unlike the comment
            cursor.execute("DELETE FROM comment_likes WHERE user_id = %s AND comment_id = %s", (user_id, comment_id))
            conn.commit()
            message = "Comment unliked"
        else:
            print("Does not exist")
            # Like the comment
            cursor.execute("INSERT INTO comment_likes (user_id, comment_id) VALUES (%s, %s)", (user_id, comment_id))
            conn.commit()
            message = "Comment liked"

        # Get updated like count
        cursor.execute("SELECT COUNT(*) FROM comment_likes WHERE comment_id = %s", (comment_id,))
        like_count = cursor.fetchone()["count"]

        return jsonify({"message": message, "likes": like_count}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()  
        if conn:
            release_db_connection(conn)







@user_blueprint.route('/comment', methods=['POST'])
@login_required
def create_comment():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        post_id = data.get("post_id")
        content = data.get("content")

        if not user_id or not post_id or not content:
            return jsonify({"error": "Missing required fields"}), 400

        # Get username from PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
        user_result = cursor.fetchone()
        cursor.close()
        conn.close()

        username = user_result["username"] if user_result else "Unknown"

        comment_data = {
            "comment_id": str(ObjectId()),  # Convert _id to string
            "user_id": user_id,
            "username": username,
            "content": content,
            "timestamp": datetime.utcnow(),
            "likes": 0,  
            "replies": []  # Empty array for future replies
        }

        # Insert into MongoDB
        mongo.db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {"comments": comment_data}}
        )

        return jsonify({"message": "Comment added!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()  
        if conn:
            release_db_connection(conn)









@user_blueprint.route('/comments/<post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM comments WHERE post_id = %s ORDER BY created_at ASC", (post_id,))
        comments = cursor.fetchall()

        return jsonify({"comments": comments}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()  
        if conn:
            release_db_connection(conn)
