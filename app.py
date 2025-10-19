# app.py
import sqlite3

# Connect to database (will create if not exists)
conn = sqlite3.connect("transport.db", check_same_thread=False)
c = conn.cursor()

# Create drivers table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS drivers (
    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    license_number TEXT,
    mobile TEXT
)
''')

# Create vehicles table if needed
c.execute('''
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_name TEXT,
    petrol_expense REAL,
    toll_expense REAL,
    maintenance_expense REAL,
    month TEXT
)
''')

conn.commit()

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# -------- Database setup --------
conn = sqlite3.connect("transport.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS drivers (
                driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                license_number TEXT,
                mobile TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                date TEXT,
                petrol REAL,
                toll REAL,
                maintenance REAL,
                FOREIGN KEY(vehicle_id) REFERENCES vehicles(vehicle_id)
            )''')

conn.commit()

# -------- Admin Login --------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚛 Transport Management System")
    st.write(f"Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.subheader("👨‍💼 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
else:
    # -------- Sidebar Menu --------
    st.sidebar.title("📋 Menu")
    menu = st.sidebar.radio("Go to", ["🏠 Dashboard",
                                      "🧑‍✈️ Driver Details",
                                      "🛠️ Vehicle Maintenance & Expense",
                                      "📊 Monthly Summary",
                                      "🚪 Logout"])
    
    if menu == "🏠 Dashboard":
        st.title("👨‍💼 Admin Dashboard")
        st.write("Welcome, Admin! Manage your transport business from one place.")
    
    elif menu == "🧑‍✈️ Driver Details":
        st.title("🧑‍✈️ Driver Details")
        with st.form("add_driver"):
            name = st.text_input("Driver Name")
            license_num = st.text_input("License Number")
            mobile = st.text_input("Mobile Number")
            submitted = st.form_submit_button("Add Driver")
            if submitted:
                c.execute("INSERT INTO drivers (name, license_number, mobile) VALUES (?, ?, ?)",
                          (name, license_num, mobile))
                conn.commit()
                st.success("Driver added successfully!")

        st.subheader("Existing Drivers")
        df_drivers = pd.read_sql("SELECT * FROM drivers", conn)
        st.dataframe(df_drivers)
    
    elif menu == "🛠️ Vehicle Maintenance & Expense":
        st.title("🛠️ Vehicle Maintenance & Expense")
        # Add vehicle
        with st.form("add_vehicle"):
            vehicle_name = st.text_input("Vehicle Name")
            v_submitted = st.form_submit_button("Add Vehicle")
            if v_submitted:
                c.execute("INSERT INTO vehicles (name) VALUES (?)", (vehicle_name,))
                conn.commit()
                st.success("Vehicle added successfully!")
        # List vehicles
        df_vehicles = pd.read_sql("SELECT * FROM vehicles", conn)
        st.subheader("Vehicles")
        st.dataframe(df_vehicles)

        # Add expense
        with st.form("add_expense"):
            vehicle_id = st.selectbox("Select Vehicle ID", df_vehicles['vehicle_id'] if not df_vehicles.empty else [])
            expense_date = st.date_input("Expense Date", date.today())
            petrol = st.number_input("Petrol Expense", 0.0)
            toll = st.number_input("Tollgate Expense", 0.0)
            maintenance = st.number_input("Maintenance Expense", 0.0)
            e_submitted = st.form_submit_button("Add Expense")
            if e_submitted:
                c.execute("""INSERT INTO expenses (vehicle_id, date, petrol, toll, maintenance)
                             VALUES (?, ?, ?, ?, ?)""",
                          (vehicle_id, expense_date, petrol, toll, maintenance))
                conn.commit()
                st.success("Expense added successfully!")

        st.subheader("Expenses")
        df_expenses = pd.read_sql("SELECT * FROM expenses", conn)
        st.dataframe(df_expenses)
    
    elif menu == "📊 Monthly Summary":
        st.title("📊 Monthly Summary")
        df = pd.read_sql("SELECT date, SUM(petrol+toll+maintenance) as total_expense FROM expenses GROUP BY date", conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            fig = px.bar(df, x='date', y='total_expense', title="Daily Expenses")
            st.plotly_chart(fig)
        else:
            st.info("No expense data available.")

    elif menu == "🚪 Logout":
        st.session_state.logged_in = False
        st.rerun()
