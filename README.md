
# Distributed EHR System - README

## Table of Contents
1. [Setup Instructions](#setup-instructions)
2. [Introduction](#introduction)
3. [Features](#features)
4. [System Architecture](#system-architecture)
5. [Backend APIs](#backend-apis)
6. [Frontend Interface](#frontend-interface)
7. [Sharding and Utilities](#sharding-and-utilities)
8. [Development Guidelines](#development-guidelines)
9. [License](#license)

---

## Setup Instructions

### Prerequisites:
- Python 3.8+
- MongoDB instance (Cloud or Local)
- PostgreSQL instance
- `pip` for package management

### Installation:
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the backend server:
   ```bash
   python backend.py
   ```
4. Launch the Streamlit frontend:
   ```bash
   streamlit run frontend.py
   ```

---

## Introduction
The Distributed EHR System is designed to manage and analyze electronic health records (EHRs) in a scalable, distributed, and fault-tolerant manner. It integrates:
- **MongoDB** for distributed NoSQL data storage
- **PostgreSQL** for relational data
- **Streamlit** for an intuitive frontend interface

This system supports data sharding, replica management, and advanced analytics, providing a robust solution for healthcare data management.

---

## Features

### Backend:
- CRUD operations for patient records
- Combined queries across MongoDB and PostgreSQL
- Analytics for admissions and billing
- Sharding and replica consistency management
- Performance comparison of sharded vs non-sharded data
- Query failover mechanism for fault tolerance

### Frontend:
- Doctor and Admin dashboards
- Patient management (Add, Update, Delete, Search)
- Distributed analytics for partitioning and sharding
- Replica management and consistency visualization

---

## System Architecture
The system comprises:
1. **Backend API**:
   - Flask application with endpoints for data access, analytics, and distributed features
   - Integration with MongoDB (NoSQL) and PostgreSQL (RDBMS)
2. **Frontend**:
   - Streamlit app providing an interface for users (Doctors, Admins)
3. **Sharding Utility**:
   - Data distribution and performance optimization across MongoDB shards

---

## Backend APIs

### Patient Management:
- `POST /patients`: Add a patient.
- `GET /combined/<patient_id>`: Fetch combined patient data.
- `PUT /patients/<patient_id>`: Update patient details.
- `DELETE /patients/<patient_id>`: Delete a patient.

### Analytics:
- `GET /analytics/admissions`: Admission data grouped by departments.
- `GET /analytics/billing`: Billing data grouped by payment status.

### Sharding:
- `GET /shard/patient/<patient_id>`: Fetch patient data from the appropriate shard.
- `GET /analytics/shards/performance`: Performance metrics of sharded vs non-sharded queries.

### Replica Management:
- `POST /replica/simulate_failure`: Simulate a replica failure.
- `POST /replica/restore`: Restore a replica.
- `GET /replica/health`: Check replica health status.

---

## Frontend Interface

### Doctor Dashboard:
- **Search Patients**: View comprehensive patient details.
- **Add Patients**: Add new patients to the system.
- **Update Patients**: Modify existing patient details.
- **Delete Patients**: Remove patients from the system.

### Admin Dashboard:
- View admissions and billing data.
- Analyze query performance improvements through partitioning and sharding.

### Distributed Analytics:
- Compare performance between sharded and non-sharded queries.
- Analyze shard distributions and throughput improvements.
- Manage replica health and query consistency.

---

## Sharding and Utilities

### Sharding:
- Patients are distributed across shards based on their ID.
- Use the `Sharding.py` script to pre-shard data and analyze shard performance.

### Utilities:
- `utils.py` provides helper functions for:
  - MongoDB and PostgreSQL connection setup.
  - Determining shards for patients.
  - Measuring query performance and shard distributions.

---

## Development Guidelines

1. **Code Structure**:
   - Keep backend logic modular in `backend.py` and utilities in `utils.py`.
   - Separate database logic from API endpoints.
2. **Error Handling**:
   - Handle exceptions gracefully in all API endpoints.
   - Provide meaningful error messages to the frontend.
3. **Testing**:
   - Test endpoints using tools like Postman or Curl.
   - Validate frontend functionality in the Streamlit interface.

---

## License
This project is licensed under the MIT License. For more details, refer to the `LICENSE` file.
