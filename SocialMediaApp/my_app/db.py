import os
import psycopg2
from psycopg2 import pool
from flask_pymongo import PyMongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}

# Initialize PostgreSQL Connection Pool
try:
    postgres_pool = pool.SimpleConnectionPool(1, 10, **POSTGRES_CONFIG)
    print("PostgreSQL connection pool created successfully!")
except Exception as e:
    print(f"Error creating PostgreSQL connection pool: {e}")
    postgres_pool = None

# Function to get a PostgreSQL connection
def get_db_connection():
    if postgres_pool:
        return postgres_pool.getconn()
    else:
        print("No database connection available!")
        return None

# Function to release the PostgreSQL connection
def release_db_connection(conn):
    if conn and postgres_pool:
        postgres_pool.putconn(conn)

# MongoDB Setup
DB_NAME = "socialmedia"
MONGO_URI = f"mongodb://localhost:27017/{DB_NAME}"
mongo = PyMongo()
