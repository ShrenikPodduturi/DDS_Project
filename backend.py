from flask import Flask, jsonify, request
from pymongo import MongoClient
from utils import get_shard_for_patient
import psycopg2
from decouple import config
import time
from pymongo.read_preferences import ReadPreference

app = Flask(__name__)

# MongoDB connection setup
mongo_client = MongoClient("mongodb+srv://sbajaj21:1DcvjYusvp1SVLcx@cluster0.da068.mongodb.net/?retryWrites=true&w=majority")
secondary_client_1 = MongoClient(
    "mongodb+srv://sbajaj21:1DcvjYusvp1SVLcx@cluster0.da068.mongodb.net/?retryWrites=true&w=majority",
    read_preference=ReadPreference.SECONDARY
)
secondary_client_2 = MongoClient(
    "mongodb+srv://sbajaj21:1DcvjYusvp1SVLcx@cluster0.da068.mongodb.net/?retryWrites=true&w=majority",
    read_preference=ReadPreference.SECONDARY_PREFERRED
)

# In-memory status for replicas
replica_status = {
    "primary": True,
    "secondary_1": True,
    "secondary_2": True,
}

mongo_db = mongo_client["ehr_system"]
patients_collection = mongo_db["patients"]

# Postgres connection setup
def connect_to_postgres():
    return psycopg2.connect(
        dbname=config("DB_NAME"),
        user=config("DB_USER"),
        password=config("DB_PASSWORD"),
        host=config("DB_HOST"),
        port=config("DB_PORT")
    )

# Combined Results API
@app.route('/combined/<patient_id>', methods=['GET'])
def get_combined_patient_data(patient_id):
    try:
        # Fetch from MongoDB
        patient_data = patients_collection.find_one({"patient_id": patient_id}, {"_id": 0})

        # Fetch from Postgres
        conn = connect_to_postgres()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM admissions WHERE patient_id = %s;", (patient_id,))
        admissions_data = cursor.fetchall()

        cursor.execute("SELECT * FROM billing WHERE patient_id = %s;", (patient_id,))
        billing_data = cursor.fetchall()

        cursor.close()
        conn.close()

        if not patient_data:
            return jsonify({"error": "Patient not found"}), 404

        return jsonify({
            "patient_details": patient_data,
            "admissions": admissions_data,
            "billing": billing_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Add Patient
@app.route('/patients', methods=['POST'])
def add_patient():
    try:
        patient_data = request.json
        if not patient_data or not patient_data.get("patient_id"):
            return jsonify({"error": "Invalid input"}), 400
        patients_collection.insert_one(patient_data)
        return jsonify({"message": "Patient added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update Patient
@app.route('/patients/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    try:
        update_data = request.json
        if not update_data:
            return jsonify({"error": "Invalid input"}), 400
        result = patients_collection.update_one({"patient_id": patient_id}, {"$set": update_data})
        if result.matched_count == 0:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({"message": "Patient updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete Patient
@app.route('/patients/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        result = patients_collection.delete_one({"patient_id": patient_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({"message": "Patient deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# All Admissions API
@app.route('/admissions', methods=['GET'])
def get_admissions():
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admissions;")
        admissions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(admissions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# All Billing API
@app.route('/billing', methods=['GET'])
def get_billing():
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM billing;")
        billing = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(billing), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Query Performance API
@app.route('/query_performance', methods=['GET'])
def query_performance():
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()

        # Query for partitioned table
        start_time = time.time()
        cursor.execute("""
            SELECT * 
            FROM admissions
            WHERE admission_date BETWEEN '2023-01-01' AND '2023-12-31';
        """)
        partitioned_time = time.time() - start_time

        # Query for non-partitioned table
        start_time = time.time()
        cursor.execute("""
            SELECT * 
            FROM admissions_non_partitioned
            WHERE admission_date BETWEEN '2023-01-01' AND '2023-12-31';
        """)
        non_partitioned_time = time.time() - start_time

        cursor.close()
        conn.close()

        return jsonify({
            "partitioned": {
                "time": partitioned_time,
                "plan": ["Simulated execution plan for partitioned table"]
            },
            "non_partitioned": {
                "time": non_partitioned_time,
                "plan": ["Simulated execution plan for non-partitioned table"]
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Analytics API for Admissions
@app.route('/analytics/admissions', methods=['GET'])
def admissions_analytics():
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()
        cursor.execute("SELECT hospital_department, COUNT(*) FROM admissions GROUP BY hospital_department;")
        analytics = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Analytics API for Billing
@app.route('/analytics/billing', methods=['GET'])
def billing_analytics():
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()
        cursor.execute("SELECT payment_status, COUNT(*) FROM billing GROUP BY payment_status;")
        analytics = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
NUM_SHARDS = 4  # Number of shards
shards = {
    f"shard_{i}": mongo_db[f"shard_{i}"] for i in range(NUM_SHARDS)
}

# Function to fetch the appropriate shard for a patient
def get_shard(patient_id):
    shard_name = get_shard_for_patient(patient_id, NUM_SHARDS)
    return shards[shard_name]


# Query Sharded Data by Patient ID
@app.route('/shard/patient/<patient_id>', methods=['GET'])
def query_shard_by_patient_id(patient_id):
    """Query a specific shard by patient ID."""
    try:
        shard_name = get_shard_for_patient(patient_id)
        data = shards[shard_name].find_one({"patient_id": patient_id}, {"_id": 0})

        if not data:
            return jsonify({"error": "Patient not found in sharded collection"}), 404

        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/analytics/shards/performance', methods=['GET'])
def shard_performance_analysis():
    try:
        # Measure query time for non-sharded collection
        start_time = time.time()
        all_patients = list(patients_collection.find({"patient_id": {"$regex": "^a"}}))
        non_sharded_query_time = time.time() - start_time

        # Measure query time for sharded collections
        sharded_query_time = 0
        for shard_name, shard_collection in shards.items():
            start_time = time.time()
            # Query only relevant shards based on pattern
            list(shard_collection.find({"patient_id": {"$regex": "^a"}}))
            sharded_query_time += time.time() - start_time

        # Data distribution across shards
        shard_distribution = {
            shard_name: shard_collection.count_documents({})
            for shard_name, shard_collection in shards.items()
        }

        # Precompute throughput improvement
        total_records = sum(shard_distribution.values())
        throughput_improvement = (total_records / sharded_query_time) / (total_records / non_sharded_query_time)

        analytics = {
            "non_sharded_query_time": non_sharded_query_time,
            "sharded_query_time": sharded_query_time,
            "shard_distribution": shard_distribution,
            "throughput_improvement": throughput_improvement,
        }

        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/replica/fixed_update', methods=['POST'])
def fixed_update():
    """Update patient data on primary replica and simulate a consistency demonstration."""
    try:
        data = request.json
        patient_id = data.get("patient_id")
        new_name = data.get("new_name")
        new_age = data.get("new_age")

        if not patient_id or not new_name or new_age is None:
            return jsonify({"error": "Invalid input"}), 400

        # Fetch existing data
        patient = primary_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Set before_update and after_update fields
        before_update = {
            "name": patient.get("name", "N/A"),
            "age": patient.get("age", "N/A")
        }
        after_update = {"name": new_name, "age": new_age}

        # Update the primary replica
        primary_collection.update_one(
            {"patient_id": patient_id},
            {"$set": {
                "name": new_name,
                "age": new_age,
                "before_update": before_update,
                "after_update": after_update
            }}
        )

        return jsonify({"message": "Update successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




primary_collection = mongo_client["ehr_system"]["patients"]
secondary_collection_1 = secondary_client_1["ehr_system"]["patients"]
secondary_collection_2 = secondary_client_2["ehr_system"]["patients"]



@app.route('/replica/compare', methods=['GET'])
def compare_replicas():
    """Fetch and compare patient data across replicas."""
    try:
        # Get Patient ID from query parameters
        patient_id = request.args.get("patient_id")
        if not patient_id:
            return jsonify({"error": "Patient ID is required"}), 400

        # Fetch records from primary and secondary replicas
        primary = primary_collection.find_one({"patient_id": patient_id}, {"_id": 0})
        secondary_1 = secondary_collection_1.find_one({"patient_id": patient_id}, {"_id": 0})
        secondary_2 = secondary_collection_2.find_one({"patient_id": patient_id}, {"_id": 0})

        if not primary:
            return jsonify({"error": "Patient not found in primary replica"}), 404

        # Add before_update and after_update if they are missing
        primary.setdefault("before_update", {})
        primary.setdefault("after_update", {})

        # Handle secondaries gracefully
        secondary_1 = secondary_1 or {}
        secondary_2 = secondary_2 or {}
        secondary_1.setdefault("before_update", {})
        secondary_1.setdefault("after_update", {})
        secondary_2.setdefault("before_update", {})
        secondary_2.setdefault("after_update", {})

        # Structure the response
        response = {
            "primary_before": primary["before_update"],
            "primary_after": primary["after_update"],
            "secondary_1_before": secondary_1["before_update"],
            "secondary_1_after": secondary_1["after_update"],
            "secondary_2_before": secondary_2["before_update"],
            "secondary_2_after": secondary_2["after_update"]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/replica/simulate_failure', methods=['POST'])
def simulate_failure():
    """Simulate a replica going offline."""
    replica = request.json.get("replica")
    if replica not in replica_status:
        return jsonify({"error": "Invalid replica name"}), 400

    # Mark replica as offline
    replica_status[replica] = False
    return jsonify({"message": f"{replica} marked as offline"}), 200


# Endpoint to restore a replica
@app.route('/replica/restore', methods=['POST'])
def restore_replica():
    """Restore a previously offline replica."""
    replica = request.json.get("replica")
    if replica not in replica_status:
        return jsonify({"error": "Invalid replica name"}), 400

    # Mark replica as online
    replica_status[replica] = True
    return jsonify({"message": f"{replica} restored"}), 200


# Endpoint to check replica health
@app.route('/replica/health', methods=['GET'])
def check_replica_health():
    """Check the health status of all replicas."""
    health_status = {}
    for replica, is_online in replica_status.items():
        health_status[replica] = "Available" if is_online else "Unavailable"

    return jsonify(health_status), 200


# Query handling considering replica status
@app.route('/replica/query', methods=['GET'])
def query_with_failover():
    """Perform a query with failover support."""
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    # Try querying the replicas based on their status
    try:
        if replica_status["primary"]:
            return jsonify(primary_collection.find_one({"patient_id": patient_id}, {"_id": 0})), 200
        elif replica_status["secondary_1"]:
            return jsonify(secondary_collection_1.find_one({"patient_id": patient_id}, {"_id": 0})), 200
        elif replica_status["secondary_2"]:
            return jsonify(secondary_collection_2.find_one({"patient_id": patient_id}, {"_id": 0})), 200
        else:
            return jsonify({"error": "No replicas are available"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
