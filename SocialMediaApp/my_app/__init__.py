from flask import Flask
from flask_pymongo import PyMongo
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL Credentials
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

def connect_postgres():
    try:
        conn = psycopg2.connect(POSTGRES_URI)
        print("Connected to PostgreSQL successfully!")
        return conn
    except Exception as e:
        print(f"PostgreSQL Connection Error: {e}")
        return None

def create_app():
    # Initialize the Flask app.
    app = Flask(__name__)

    # Load secret key from .env
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Configure MongoDB
    app.config["MONGO_URI"] = MONGO_URI
    mongo.init_app(app)

    return app
