import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Transport Management System", layout="wide")

# --------------------------
# Database setup
# --------------------------
conn = sqlite3.connect("transport.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''
CREATE TABLE IF NOT EXISTS drivers (
    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    license_number TEXT,
    mobile TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    petrol_expense REAL DEFAULT 0,
    toll_expense REAL DEFAULT 0,
    maintenance_expense REAL DEFAULT 0,
    month TEXT
)
''')

conn.commit()

# --------------------------
# Helper functions
# --------------------------
def insert_driver(name, license_number, mobile):
    c.execute("INSERT INTO drivers (name, license_number, mobile) VALUES (?, ?, ?)",
              (name, license_number, mobile))
    conn.commit()

def insert_vehicle(name):
    month = datetime.now().strftime("%Y-%m")
    # Ensure table exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            petrol_expense REAL DEFAULT 0,
            toll_expense REAL DEFAULT 0,
            maintenance_expense REAL DEFAULT 0,
            month TEXT
        )
    ''')
    c.execute("INSERT INTO vehicles (name, month) VALUES (?, ?)", (name, month))
    conn.commit()

def update_vehicle_expense(vehicle_id, petrol, toll, maintenance):
    c.execute('''
        UPDATE vehicles
        SET petrol_expense = ?, toll_expense = ?, maintenance_expense = ?
        WHERE vehicle_id = ?
    ''', (petrol, toll, maintenance, vehicle_id))
    conn.commit()

def get_drivers():
    df = pd.read_sql_query("SELECT * FROM drivers", conn)
    return df

def get_vehicles():
    df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    return df

# --------------------------
# Sidebar menu
# --------------------------
menu = ["Dashboard", "Driver Details", "Vehicle Maintenance & Expense", "Monthly Summary", "Logout"]
choice = st.sidebar.selectbox("📋 Menu", menu)

# --------------------------
# Dashboard
# --------------------------
if choice == "Dashboard":
    st.title("👨‍💼 Admin Dashboard")
    st.write("Welcome, Admin! Manage your transport business from one place.")
    st.write(f"**Date & Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --------------------------
# Driver Details
# --------------------------
elif choice == "Driver Details":
    st.title("🧑‍✈️ Driver Personal Details")
    
    st.subheader("Add New Driver")
    name = st.text_input("Driver Name")
    license_number = st.text_input("License Number")
    mobile = st.text_input("Mobile Number")
    if st.button("Add Driver"):
        insert_driver(name, license_number, mobile)
        st.success(f"Driver '{name}' added successfully!")

    st.subheader("All Drivers")
    drivers_df = get_drivers()
    st.dataframe(drivers_df)

# --------------------------
# Vehicle Maintenance & Expense
# --------------------------
elif choice == "Vehicle Maintenance & Expense":
    st.title("🛠️ Vehicle Maintenance & Expense")
    
    st.subheader("Add New Vehicle")
    vehicle_name = st.text_input("Vehicle Name")
    if st.button("Add Vehicle"):
        insert_vehicle(vehicle_name)
        st.success(f"Vehicle '{vehicle_name}' added successfully!")
    
    st.subheader("Update Vehicle Expenses")
    vehicles_df = get_vehicles()
    st.dataframe(vehicles_df)
    
    if not vehicles_df.empty:
        selected_vehicle = st.selectbox("Select Vehicle to Update", vehicles_df['vehicle_id'])
        petrol = st.number_input("Petrol Expense", min_value=0.0, step=0.1)
        toll = st.number_input("Toll Expense", min_value=0.0, step=0.1)
        maintenance = st.number_input("Maintenance Expense", min_value=0.0, step=0.1)
        if st.button("Update Expenses"):
            update_vehicle_expense(selected_vehicle, petrol, toll, maintenance)
            st.success("Vehicle expenses updated successfully!")

# --------------------------
# Monthly Summary
# --------------------------
elif choice == "Monthly Summary":
    st.title("📊 Monthly Expense Summary")
    vehicles_df = get_vehicles()
    if not vehicles_df.empty:
        vehicles_df['total_expense'] = vehicles_df['petrol_expense'] + vehicles_df['toll_expense'] + vehicles_df['maintenance_expense']
        fig = px.bar(vehicles_df, x='name', y='total_expense', title="Total Expenses per Vehicle")
        st.plotly_chart(fig)
        st.dataframe(vehicles_df[['name','petrol_expense','toll_expense','maintenance_expense','total_expense','month']])

# --------------------------
# Logout
# --------------------------
elif choice == "Logout":
    st.warning("You have logged out!")
