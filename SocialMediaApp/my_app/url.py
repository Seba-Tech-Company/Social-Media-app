from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

@app.route('/create_post', methods=['POST'])
def create_post():
    try:
        user_id = request.form.get("user_id")
        content = request.form.get("content")
        media_file = request.files.get("media")

        if not user_id or not content:
            return jsonify({"error": "Missing user_id or content"}), 400

        media_filename = None
        if media_file:
            media_filename = secure_filename(media_file.filename)
            media_path = os.path.join(app.config['UPLOAD_FOLDER'], media_filename)
            media_file.save(media_path)

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Insert post into database
        query = """
            INSERT INTO posts (user_id, content, media, likes) 
            VALUES (%s, %s, %s, %s) RETURNING *
        """
        cursor.execute(query, (user_id, content, media_filename, 0))
        new_post = cursor.fetchone()
        conn.commit()

        return jsonify({"message": "Post created successfully", "post": new_post}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
