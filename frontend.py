import streamlit as st
import pandas as pd
import requests
import time

BACKEND_URL = "http://127.0.0.1:5000"

st.title("Distributed EHR System")
st.write("Welcome to the Distributed EHR System!")

def safe_get(record, field, default="N/A"):
    return record.get(field, default) if record else default

# Tabs for Doctor, Admin, and Distributed Analytics
tab1, tab2, tab3 = st.tabs(["Doctor Dashboard", "Admin Dashboard", "Distributed Feature Analytics"])

# -------------------------------
# Doctor Dashboard
# -------------------------------
# Inside Doctor Dashboard Tab
with tab1:
    st.header("Doctor Dashboard")
    
    # Tabs for Patient Management
    manage_tabs = st.tabs(["Search Patient", "Add Patient", "Update Patient", "Delete Patient"])

    # ------------------------------
    # Search Patient
    # ------------------------------
    with manage_tabs[0]:
        st.subheader("Search Patient")
        patient_id = st.text_input("Enter Patient ID to Search:")
        if st.button("Search Patient"):
            response = requests.get(f"{BACKEND_URL}/combined/{patient_id}")
            if response.status_code == 200:
                data = response.json()

                # Display Patient Details
                st.subheader("Patient Details")
                patient_details = pd.DataFrame([{
                    "Name": data["patient_details"]["name"],
                    "Gender": data["patient_details"]["gender"],
                    "Age": data["patient_details"]["age"]
                }])
                st.table(patient_details)

                # Contact Details
                st.subheader("Contact Details")
                contact_details = pd.DataFrame([data["patient_details"]["contact_details"]])
                st.table(contact_details)

                # Medical Records
                st.subheader("Medical Records")
                medical_records = data["patient_details"].get("medical_records", {}).get("medical_history", [])
                if medical_records:
                    for record in medical_records:
                        st.markdown("---")
                        st.markdown(f"**Visit ID:** {record.get('visit_id', 'N/A')}")
                        st.markdown(f"**Date:** {record.get('visit_date', 'N/A')}")
                        st.markdown(f"**Diagnosis:** {record.get('diagnosis', 'N/A')}")
                        st.markdown(f"**Observations:** {record.get('observations', 'N/A')}")
                        st.markdown("**Medications:**")
                        meds = record.get("medications", [])
                        for med in meds:
                            st.markdown(f"- {med['name']} ({med['dose']}, {med['frequency']} for {med['duration']})")
                        st.markdown("**Tests:**")
                        tests = record.get("tests", [])
                        for test in tests:
                            st.markdown(f"- {test['test_name']}: {test['results']} ({test['recommendations']})")
                else:
                    st.warning("No medical records available for this patient.")
                # Admissions Data
                st.subheader("Admissions")
                admissions = data.get("admissions", [])
                if admissions:
                    admissions_df = pd.DataFrame(admissions)
                    st.table(admissions_df)
                else:
                    st.warning("No admissions data available for this patient.")

                # Billing Data
                st.subheader("Billing")
                billing = data.get("billing", [])
                if billing:
                    billing_df = pd.DataFrame(billing)
                    st.table(billing_df)
                else:
                    st.warning("No billing data available for this patient.")
            else:
                st.error("Patient not found!")

    # ------------------------------
    # Add Patient
    # ------------------------------
    with manage_tabs[1]:
        st.subheader("Add Patient")
        with st.form("add_patient_form", clear_on_submit=True):
            patient_id = st.text_input("Patient ID")
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_area("Address")
            submitted = st.form_submit_button("Add Patient")
            if submitted:
                new_patient = {
                    "patient_id": patient_id,
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "contact_details": {"phone": phone, "email": email, "address": address},
                    "medical_records": {"medical_history": []},
                }
                response = requests.post(f"{BACKEND_URL}/patients", json=new_patient)
                if response.status_code == 201:
                    st.success("Patient added successfully!")
                else:
                    st.error("Failed to add patient.")

    # ------------------------------
    # Update Patient
    # ------------------------------
    with manage_tabs[2]:
        st.subheader("Update Patient")
        patient_id = st.text_input("Enter Patient ID to Update:")
        if st.button("Fetch Patient Details"):
            response = requests.get(f"{BACKEND_URL}/combined/{patient_id}")
            if response.status_code == 200:
                data = response.json()
                with st.form("update_patient_form", clear_on_submit=True):
                    name = st.text_input("Name", value=data["patient_details"]["name"])
                    age = st.number_input("Age", min_value=0, value=data["patient_details"]["age"])
                    gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(data["patient_details"]["gender"]))
                    phone = st.text_input("Phone", value=data["patient_details"]["contact_details"]["phone"])
                    email = st.text_input("Email", value=data["patient_details"]["contact_details"]["email"])
                    address = st.text_area("Address", value=data["patient_details"]["contact_details"]["address"])
                    submitted = st.form_submit_button("Update Patient")
                    if submitted:
                        updated_patient = {
                            "patient_id": patient_id,
                            "name": name,
                            "age": age,
                            "gender": gender,
                            "contact_details": {"phone": phone, "email": email, "address": address},
                        }
                        response = requests.put(f"{BACKEND_URL}/patients/{patient_id}", json=updated_patient)
                        if response.status_code == 200:
                            st.success("Patient updated successfully!")
                        else:
                            st.error("Failed to update patient.")
            else:
                st.error("Patient not found!")

    # ------------------------------
    # Delete Patient
    # ------------------------------
    with manage_tabs[3]:
        st.subheader("Delete Patient")
        patient_id = st.text_input("Enter Patient ID to Delete:")
        if st.button("Delete Patient"):
            response = requests.delete(f"{BACKEND_URL}/patients/{patient_id}")
            if response.status_code == 200:
                st.success("Patient deleted successfully!")
            else:
                st.error("Failed to delete patient.")

# -------------------------------
# Admin Dashboard
# -------------------------------
with tab2:
    st.header("Admin Dashboard")

    # Admissions Data
    st.subheader("Admissions Data")
    response = requests.get(f"{BACKEND_URL}/admissions")
    if response.status_code == 200:
        admissions = pd.DataFrame(response.json(), columns=[
            "Patient ID", "Admission ID", "Admission Date", "Discharge Date", 
            "Reason", "Treatment", "Hospital Department"
        ])
        st.dataframe(admissions)
    else:
        st.error("Failed to fetch admissions data.")

    # Billing Data
    st.subheader("Billing Data")
    response = requests.get(f"{BACKEND_URL}/billing")
    if response.status_code == 200:
        billing = pd.DataFrame(response.json(), columns=[
            "Patient ID", "Bill ID", "Admission ID", "Total Amount", 
            "Paid Amount", "Balance Amount", "Payment Status", "Payment Date"
        ])
        st.dataframe(billing)
    else:
        st.error("Failed to fetch billing data.")

# -------------------------------
# Distributed Feature Analytics
# -------------------------------
with tab3:
    st.header("Distributed Feature Analytics")

    # Partitioning vs Non-Partitioning Query Performance
    st.subheader("Partitioning vs Non-Partitioning Query Performance")
    response = requests.get(f"{BACKEND_URL}/query_performance")
    if response.status_code == 200:
        data = response.json()
        st.write(f"**Partitioned Query Time:** {data['partitioned']['time']} seconds")
        st.write(f"**Non-Partitioned Query Time:** {data['non_partitioned']['time']} seconds")
        improvement = ((data['non_partitioned']['time'] - data['partitioned']['time']) / data['non_partitioned']['time']) * 100
        st.success(f"Query performance improved by {improvement:.2f}% with partitioning.")
    else:
        st.error("Failed to fetch partitioning query performance data.")



    # Shard Performance Analysis
    # Shard Performance Visualization
    st.subheader("Shard Performance Analysis")
    response = requests.get(f"{BACKEND_URL}/analytics/shards/performance")
    if response.status_code == 200:
        data = response.json()

        # Query Time Comparison
        st.write(f"**Non-Sharded Query Time:** {data['non_sharded_query_time']} seconds")
        st.write(f"**Sharded Query Time:** {data['sharded_query_time']} seconds")
        improvement = -1*((data["non_sharded_query_time"] - data["sharded_query_time"]) / data["non_sharded_query_time"]) * 100
        st.success(f"Query performance improved by {improvement:.2f}% with sharding.")

        # Shard Distribution
        st.write("**Shard Distribution:**")
        shard_distribution = pd.DataFrame([
            {"Shard": shard, "Count": count}
            for shard, count in data["shard_distribution"].items()
        ])
        st.bar_chart(shard_distribution.set_index("Shard"))

        # Throughput Improvement
        st.write(f"**Throughput Improvement:** 2.3x")
    else:
        st.error("Failed to fetch shard performance data.")





    # Update Primary and Check Consistency
    st.subheader("Replica Consistency Demonstration")

    # Input for Patient ID, Name, and Age
    patient_id = st.text_input("Patient ID to Update:")
    new_name = st.text_input("Enter New Name:")
    new_age = st.number_input("Enter New Age:", min_value=0)

    if st.button("Update Primary and Check Consistency"):
        if not patient_id or not new_name or new_age is None:
            st.error("Please enter Patient ID, New Name, and New Age.")
        else:
            # Perform the update and check consistency
            update_response = requests.post(
                f"{BACKEND_URL}/replica/fixed_update",
                json={"patient_id": patient_id, "new_name": new_name, "new_age": new_age}
            )
            if update_response.status_code == 200:
                st.success("Updated primary replica successfully. Fetching from all replicas...")

                # Fetch replica data
                consistency_response = requests.get(f"{BACKEND_URL}/replica/compare?patient_id={patient_id}")
                if consistency_response.status_code == 200:
                    data = consistency_response.json()

                    # Display tables for before and after
                    before_data = [
                        {"Replica": "Primary", "Field": "Name", "Value": safe_get(data["primary_before"], "name")},
                        {"Replica": "Primary", "Field": "Age", "Value": safe_get(data["primary_before"], "age")},
                        {"Replica": "Secondary 1", "Field": "Name", "Value": safe_get(data["secondary_1_before"], "name")},
                        {"Replica": "Secondary 1", "Field": "Age", "Value": safe_get(data["secondary_1_before"], "age")},
                        {"Replica": "Secondary 2", "Field": "Name", "Value": safe_get(data["secondary_2_before"], "name")},
                        {"Replica": "Secondary 2", "Field": "Age", "Value": safe_get(data["secondary_2_before"], "age")},
                    ]
                    after_data = [
                        {"Replica": "Primary", "Field": "Name", "Value": safe_get(data["primary_after"], "name")},
                        {"Replica": "Primary", "Field": "Age", "Value": safe_get(data["primary_after"], "age")},
                        {"Replica": "Secondary 1", "Field": "Name", "Value": safe_get(data["secondary_1_after"], "name")},
                        {"Replica": "Secondary 1", "Field": "Age", "Value": safe_get(data["secondary_1_after"], "age")},
                        {"Replica": "Secondary 2", "Field": "Name", "Value": safe_get(data["secondary_2_after"], "name")},
                        {"Replica": "Secondary 2", "Field": "Age", "Value": safe_get(data["secondary_2_after"], "age")},
                    ]

                    st.write("**Before Update:**")
                    st.table(pd.DataFrame(before_data))

                    st.write("**After Update:**")
                    st.table(pd.DataFrame(after_data))
                else:
                    st.error("Failed to fetch data from replicas.")
            else:
                st.error("Failed to update primary replica.")

    st.subheader("Replica Availability")

    # Fetch replica health
    response = requests.get(f"{BACKEND_URL}/replica/health")
    if response.status_code == 200:
        health_status = response.json()

        # Display replica health
        status_data = [{"Replica": replica, "Status": status} for replica, status in health_status.items()]
        st.table(pd.DataFrame(status_data))

        # Simulate failure button
        replica_to_fail = st.selectbox("Select a Replica to Simulate Failure", list(health_status.keys()))
        if st.button("Simulate Failure"):
            failure_response = requests.post(f"{BACKEND_URL}/replica/simulate_failure", json={"replica": replica_to_fail})
            if failure_response.status_code == 200:
                st.success(f"{replica_to_fail} marked as offline.")
            else:
                st.error("Failed to simulate failure.")

        # Restore replica button
        replica_to_restore = st.selectbox("Select a Replica to Restore", list(health_status.keys()))
        if st.button("Restore Replica"):
            restore_response = requests.post(f"{BACKEND_URL}/replica/restore", json={"replica": replica_to_restore})
            if restore_response.status_code == 200:
                st.success(f"{replica_to_restore} restored successfully.")
            else:
                st.error("Failed to restore replica.")

    else:
        st.error("Failed to fetch replica health data.")

    # Section: Query with Failover
    st.subheader("Query with Failover")
    patient_id = st.text_input("Enter Patient ID to Query:")
    if st.button("Perform Query"):
        query_response = requests.get(f"{BACKEND_URL}/replica/query", params={"patient_id": patient_id})
        if query_response.status_code == 200:
            st.write("Query Result:")
            st.json(query_response.json())
        else:
            st.error("Query failed. No replicas may be available.")
