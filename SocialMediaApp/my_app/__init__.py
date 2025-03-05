import psycopg2
import os
from flask import Flask, render_template
from flask_pymongo import PyMongo
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL Credentials
POSTGRES_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}

# Initializing postgre connection pool
postgres_pool = pool.SimpleConnectionPool(1, 10, **POSTGRES_CONFIG)

def get_db_connection():
    # Get a connection from the PostgreSQL pool
    try:
        return postgres_pool.getconn()
    except Exception as e:
        print(f"Error getting connection: {e}")
        return None

def release_db_connection(conn):
    # Release a connection back to the pool
    if conn:
        postgres_pool.putconn(conn)


# MongoDB Setup
DB_NAME = "socialmedia"
MONGO_URI = f"mongodb://localhost:27017/{DB_NAME}"
mongo = PyMongo()


def create_app():
    # Initializing and configuring the flask app.
    app = Flask(__name__)

    # Load secret key from .env
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Configure MongoDB
    app.config["MONGO_URI"] = MONGO_URI
    mongo.init_app(app)
    
    @app.route("/")
    def home():
        return render_template("index.html")
    
    @app.route("/signup")
    def signup():
        return render_template("Signup.html")
    
    @app.route("/signin")
    def signin():
        return render_template("Signin.html")
    
    return app
