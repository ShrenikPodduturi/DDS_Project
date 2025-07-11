from pymongo import MongoClient
import psycopg2
from decouple import config

# MongoDB connection setup
def get_mongo_client():
    """Returns a MongoDB client."""
    return MongoClient("mongodb+srv://sbajaj21:1DcvjYusvp1SVLcx@cluster0.da068.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

def get_mongo_db():
    """Returns the MongoDB database object."""
    client = get_mongo_client()
    return client["ehr_system"]

def get_shard_for_patient(patient_id, num_shards):
    """Determine the shard for a given patient ID."""
    if not patient_id:
        raise ValueError("Invalid patient ID")
    return f"shard_{hash(patient_id) % num_shards}"


def get_shards():
    """Returns a dictionary of shard collections."""
    db = get_mongo_db()
    return {
        "shard1": db["patients_shard1"],
        "shard2": db["patients_shard2"],
        "shard3": db["patients_shard3"]
    }

# Postgres connection setup
def connect_to_postgres():
    """Returns a connection object for PostgreSQL."""
    return psycopg2.connect(
        dbname=config("DB_NAME"),
        user=config("DB_USER"),
        password=config("DB_PASSWORD"),
        host=config("DB_HOST"),
        port=config("DB_PORT")
    )

# Helper functions
def calculate_hash(value, num_shards):
    """Returns a hash for the given value modulo the number of shards."""
    return hash(value) % num_shards

def get_shard_name(patient_id, shards):
    """Determines the shard for a given patient_id."""
    num_shards = len(shards)
    shard_index = calculate_hash(patient_id, num_shards)
    return f"shard{shard_index + 1}"

def measure_query_time(func):
    """Measures execution time of a function."""
    import time
    start_time = time.time()
    result = func()
    end_time = time.time()
    return result, end_time - start_time

def shard_distribution(shards):
    """Calculates the number of records in each shard."""
    return {shard_name: shard_collection.count_documents({}) for shard_name, shard_collection in shards.items()}
