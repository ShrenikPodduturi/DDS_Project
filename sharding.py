from pymongo import MongoClient
from utils import get_shard_for_patient
import time

# MongoDB connection setup
mongo_client = MongoClient("mongodb+srv://sbajaj21:1DcvjYusvp1SVLcx@cluster0.da068.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo_db = mongo_client["ehr_system"]
patients_collection = mongo_db["patients"]

NUM_SHARDS = 4  # Number of shards
shards = {
    f"shard_{i}": mongo_db[f"shard_{i}"] for i in range(NUM_SHARDS)
}

def pre_shard_patients():
    """Distribute patients into shards based on patient ID."""
    for shard in shards.values():
        shard.delete_many({})  # Clear existing data (optional)

    patients = list(patients_collection.find({}))
    for patient in patients:
        try:
            shard_name = get_shard_for_patient(patient["patient_id"], NUM_SHARDS)
            shards[shard_name].insert_one(patient)
        except Exception as e:
            print(f"Error sharding patient {patient.get('patient_id')}: {e}")

    # Check shard distribution
    for shard_name, shard_collection in shards.items():
        count = shard_collection.count_documents({})
        print(f"Shard {shard_name} has {count} records.")

def precompute_fixed_shard_performance():
    """Precompute fixed shard performance metrics for optimized query."""
    # Query filter: Target a specific range of patient IDs to optimize shard utilization
    query_filter = {"patient_id": {"$regex": "^[a-m]"}}  # Patients with IDs starting with 'a' to 'm'


    # Measure non-sharded query time
    start_time = time.time()
    list(patients_collection.find(query_filter))
    non_sharded_query_time = time.time() - start_time

    # Measure sharded query time
    sharded_query_time = 0
    for shard_name, shard_collection in shards.items():
        start_time = time.time()
        list(shard_collection.find(query_filter))
        sharded_query_time += time.time() - start_time

    # Data distribution across shards
    shard_distribution = {
        shard_name: shard_collection.count_documents({})
        for shard_name, shard_collection in shards.items()
    }

    # Throughput improvement
    total_records = sum(shard_distribution.values())
    throughput_improvement = (total_records / sharded_query_time) / (total_records / non_sharded_query_time)

    fixed_metrics = {
        "non_sharded_query_time": non_sharded_query_time,
        "sharded_query_time": sharded_query_time,
        "shard_distribution": shard_distribution,
        "throughput_improvement": throughput_improvement
    }

    print(f"Precomputed Metrics: {fixed_metrics}")
    return fixed_metrics


# Generate the fixed metrics during sharding
if __name__ == "__main__":
    pre_shard_patients()  # Ensure sharding is done
    fixed_metrics = precompute_fixed_shard_performance()
    print(f"Precomputed Metrics: {fixed_metrics}")

