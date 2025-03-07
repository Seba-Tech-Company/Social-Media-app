from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(_name_)

def get_db_connection():
    return psycopg2.connect(
        dbname="socialmedia",
        user="",
        password="",
        host="",
        port=""
    )

@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.get_json()
    
    user_id = data.get("user_id")
    content = data.get("content")
    
    if not user_id or not content:
        return jsonify({"error": "Missing user_id or content"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = "INSERT INTO posts (user_id, content) VALUES (%s, %s) RETURNING *"
        cursor.execute(query, (user_id, content))
        new_post = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Post created successfully", "post": new_post}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if _name_ == '_main_':
    app.run(debug=True)



