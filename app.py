# app_v2.py
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import io

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Transport Management System (V2)", layout="wide")

# -------------------- DATABASE --------------------
DB_PATH = "transport.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    # vehicles
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_no TEXT UNIQUE,
                    model TEXT,
                    insurance_expiry DATE
                )''')
    # drivers
    c.execute('''CREATE TABLE IF NOT EXISTS drivers (
                    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    license_no TEXT,
                    author_no TEXT,
                    contact TEXT,
                    backup_mobile TEXT,
                    assigned_vehicle TEXT
                )''')
    # expenses
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_no TEXT,
                    date TEXT,
                    petrol REAL DEFAULT 0,
                    toll REAL DEFAULT 0,
                    maintenance REAL DEFAULT 0,
                    tips REAL DEFAULT 0,
                    note TEXT
                )''')
    # attendance
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_id INTEGER,
                    date TEXT,
                    status TEXT
                )''')
    # income (business)
    c.execute('''CREATE TABLE IF NOT EXISTS income (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    amount REAL,
                    note TEXT
                )''')
    # tasks / pending work
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_no TEXT,
                    description TEXT,
                    due_date TEXT,
                    status TEXT
                )''')
    conn.commit()
    # default admin
    c.execute("INSERT OR IGNORE INTO admin (id, username, password) VALUES (1, 'admin', 'admin123')")
    conn.commit()
    conn.close()

init_db()

# -------------------- HELPERS --------------------
def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    conn.close()

def insert_expense(vehicle_no, date, petrol, toll, maintenance, tips, note):
    execute('''INSERT INTO expenses (vehicle_no, date, petrol, toll, maintenance, tips, note)
               VALUES (?, ?, ?, ?, ?, ?, ?)''', (vehicle_no, date, petrol, toll, maintenance, tips, note))

def add_driver_record(name, license_no, author_no, contact, backup_mobile, assigned_vehicle):
    execute('''INSERT INTO drivers (name, license_no, author_no, contact, backup_mobile, assigned_vehicle)
               VALUES (?, ?, ?, ?, ?, ?)''', (name, license_no, author_no, contact, backup_mobile, assigned_vehicle))

def add_vehicle_record(vehicle_no, model, insurance_expiry):
    execute('''INSERT OR IGNORE INTO vehicles (vehicle_no, model, insurance_expiry)
               VALUES (?, ?, ?)''', (vehicle_no, model, insurance_expiry))

def mark_attendance(driver_id, date, status):
    execute('''INSERT INTO attendance (driver_id, date, status) VALUES (?, ?, ?)''', (driver_id, date, status))

def add_income(date, amount, note):
    execute('''INSERT INTO income (date, amount, note) VALUES (?, ?, ?)''', (date, amount, note))

def add_task(vehicle_no, description, due_date, status="Pending"):
    execute('''INSERT INTO tasks (vehicle_no, description, due_date, status) VALUES (?, ?, ?, ?)''',
            (vehicle_no, description, due_date, status))

# -------------------- AUTH (ADMIN ONLY) --------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# header + live-ish clock (updates on interaction)
st.markdown(f"""
    <div style="padding:14px;border-radius:8px;background:linear-gradient(90deg,#0d6efd,#6610f2);color:white;">
        <h2 style="margin:0">🚛 Transport Management System — Admin</h2>
        <div style="opacity:0.95">Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)

# LOGIN PAGE
if not st.session_state.logged_in:
    st.markdown("<br>")
    st.markdown("""<div style='max-width:520px;margin:auto;padding:24px;background:#fff;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.08);'>""", unsafe_allow_html=True)
    st.subheader("🔒 Admin Login")
    col1, col2 = st.columns([2,1])
    with col1:
        username = st.text_input("Username", "")
    with col2:
        password = st.text_input("Password", "", type="password")
    if st.button("Login"):
        # check against DB (safe)
        admin_df = query_df("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        if not admin_df.empty:
            st.session_state.logged_in = True
            st.success("Login successful — welcome admin.")
            st.experimental_rerun()
        else:
            st.error("Invalid admin username or password.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# -------------------- SIDEBAR (Admin menu) --------------------
st.sidebar.title("Admin Menu")
menu = st.sidebar.radio("Go to", [
    "Dashboard",
    "Driver Management",
    "Vehicle Management",
    "Vehicle Maintenance & Expense",
    "Attendance",
    "Income & Profit/Loss",
    "Expense Reports & Charts",
    "Insurance & Alerts",
    "Pending Tasks",
    "Export Data",
    "Logout"
])

if st.sidebar.button("Refresh"):
    st.experimental_rerun()

# -------------------- DASHBOARD --------------------
if menu == "Dashboard":
    st.header("📊 Dashboard")
    # quick stats
    vehicles_df = query_df("SELECT * FROM vehicles")
    drivers_df = query_df("SELECT * FROM drivers")
    expenses_last_60 = query_df("SELECT * FROM expenses WHERE date >= ?", ((datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),))
    income_last_60 = query_df("SELECT * FROM income WHERE date >= ?", ((datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Vehicles", len(vehicles_df))
    col2.metric("Drivers", len(drivers_df))
    col3.metric("Expense entries (60d)", len(expenses_last_60))
    col4.metric("Income entries (60d)", len(income_last_60))

    st.markdown("---")
    # insurance alerts
    st.subheader("Insurance Alerts (expiring within 10 days)")
    alert_df = query_df("""SELECT vehicle_no, model, insurance_expiry 
                           FROM vehicles 
                           WHERE insurance_expiry IS NOT NULL AND insurance_expiry != '' 
                           AND date(insurance_expiry) <= date(?)""", ((datetime.now()+timedelta(days=10)).strftime("%Y-%m-%d"),))
    if not alert_df.empty:
        st.table(alert_df)
    else:
        st.success("No insurance expiry within 10 days.")

    st.subheader("Recent Expenses (last 30 days)")
    recent = query_df("SELECT * FROM expenses WHERE date >= ? ORDER BY date DESC", ((datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d"),))
    st.dataframe(recent)

# -------------------- DRIVER MANAGEMENT --------------------
elif menu == "Driver Management":
    st.header("🧑‍✈️ Driver Management")
    with st.expander("Add a new driver"):
        with st.form("driver_form", clear_on_submit=True):
            name = st.text_input("Driver Name")
            license_no = st.text_input("License Number")
            author_no = st.text_input("Author Number")
            contact = st.text_input("Contact Number")
            backup_mobile = st.text_input("Backup Family Mobile")
            vehicles = query_df("SELECT vehicle_no FROM vehicles")
            vehicle_options = vehicles['vehicle_no'].tolist() if not vehicles.empty else [f"Vehicle-{i}" for i in range(1,21)]
            assigned = st.selectbox("Assign Vehicle", [""] + vehicle_options)
            submitted = st.form_submit_button("Add Driver")
            if submitted:
                if not name or not license_no:
                    st.warning("Please provide at least driver name and license number.")
                else:
                    add_driver_record(name, license_no, author_no, contact, backup_mobile, assigned)
                    st.success(f"Driver {name} added.")
    st.markdown("---")
    st.subheader("Current Drivers")
    df = query_df("SELECT * FROM drivers")
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No drivers yet.")

# -------------------- VEHICLE MANAGEMENT --------------------
elif menu == "Vehicle Management":
    st.header("🚚 Vehicle Management")
    with st.expander("Add / Update Vehicle"):
        with st.form("vehicle_form", clear_on_submit=True):
            vno = st.text_input("Vehicle No (unique)", value="")
            model = st.text_input("Model/Name")
            ins_date = st.date_input("Insurance expiry date", value=datetime.now() + timedelta(days=365))
            submitted = st.form_submit_button("Save Vehicle")
            if submitted:
                if not vno:
                    st.warning("Vehicle number is required.")
                else:
                    add_vehicle_record(vno, model, ins_date.strftime("%Y-%m-%d"))
                    st.success(f"Vehicle {vno} saved/updated.")
    st.markdown("---")
    st.subheader("All Vehicles")
    vdf = query_df("SELECT * FROM vehicles")
    st.dataframe(vdf)

# -------------------- VEHICLE MAINTENANCE & EXPENSE --------------------
elif menu == "Vehicle Maintenance & Expense":
    st.header("🛠️ Vehicle Maintenance & Expense")
    with st.expander("Add Expense Record"):
        with st.form("expense_form", clear_on_submit=True):
            vehicles = query_df("SELECT vehicle_no FROM vehicles")
            vehicle_options = vehicles['vehicle_no'].tolist() if not vehicles.empty else [f"Vehicle-{i}" for i in range(1,21)]
            vehicle_no = st.selectbox("Vehicle", vehicle_options)
            date = st.date_input("Date", value=datetime.now())
            petrol = st.number_input("Petrol (₹)", min_value=0.0, value=0.0)
            toll = st.number_input("Toll (₹)", min_value=0.0, value=0.0)
            maintenance = st.number_input("Maintenance (₹)", min_value=0.0, value=0.0)
            tips = st.number_input("Driver Tips (₹)", min_value=0.0, value=0.0)
            note = st.text_input("Note (optional)")
            submitted = st.form_submit_button("Save Expense")
            if submitted:
                insert_expense(vehicle_no, date.strftime("%Y-%m-%d"), petrol, toll, maintenance, tips, note)
                st.success("Expense saved.")

    st.markdown("---")
    st.subheader("View Expenses (date filter)")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", datetime.now() - timedelta(days=60))
    with col2:
        end_date = st.date_input("End date", datetime.now())
    if start_date > end_date:
        st.error("Start date must be before end date.")
    else:
        df = query_df("SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                      (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        st.dataframe(df)

# -------------------- ATTENDANCE --------------------
elif menu == "Attendance":
    st.header("🧾 Driver Attendance")
    drivers = query_df("SELECT driver_id, name FROM drivers")
    if drivers.empty:
        st.info("No drivers available. Add drivers first.")
    else:
        with st.form("att_form"):
            d_map = dict(zip(drivers['driver_id'], drivers['name']))
            selected_driver = st.selectbox("Driver", drivers['driver_id'].tolist(), format_func=lambda x: f"{x} - {d_map[x]}")
            att_date = st.date_input("Date", datetime.now())
            status = st.selectbox("Status", ["Present", "Absent"])
            submitted = st.form_submit_button("Mark Attendance")
            if submitted:
                mark_attendance(selected_driver, att_date.strftime("%Y-%m-%d"), status)
                st.success("Attendance recorded.")
        st.markdown("---")
        st.subheader("Attendance (last 30 days)")
        att_df = query_df("SELECT a.id, a.driver_id, d.name, a.date, a.status FROM attendance a LEFT JOIN drivers d ON a.driver_id=d.driver_id WHERE date >= ? ORDER BY date DESC",
                          ((datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d"),))
        st.dataframe(att_df)

# -------------------- INCOME & PROFIT/LOSS --------------------
elif menu == "Income & Profit/Loss":
    st.header("💰 Income & Profit/Loss")
    with st.expander("Add Business Income"):
        with st.form("income_form"):
            i_date = st.date_input("Date", datetime.now())
            amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0)
            note = st.text_input("Note")
            submitted = st.form_submit_button("Add Income")
            if submitted:
                add_income(i_date.strftime("%Y-%m-%d"), amount, note)
                st.success("Income recorded.")

    st.markdown("---")
    st.subheader("Profit / Loss by Month")
    # prepare monthly sums
    exp_df = query_df("SELECT date, (petrol + toll + maintenance + tips) as total FROM expenses")
    if not exp_df.empty:
        exp_df['month'] = pd.to_datetime(exp_df['date']).dt.to_period('M').astype(str)
        monthly_exp = exp_df.groupby('month')['total'].sum().reset_index().rename(columns={'total':'expenses'})
    else:
        monthly_exp = pd.DataFrame(columns=['month','expenses'])
    inc_df = query_df("SELECT date, amount FROM income")
    if not inc_df.empty:
        inc_df['month'] = pd.to_datetime(inc_df['date']).dt.to_period('M').astype(str)
        monthly_inc = inc_df.groupby('month')['amount'].sum().reset_index().rename(columns={'amount':'income'})
    else:
        monthly_inc = pd.DataFrame(columns=['month','income'])
    summary = pd.merge(monthly_inc, monthly_exp, on='month', how='outer').fillna(0)
    if not summary.empty:
        summary['profit'] = summary['income'] - summary['expenses']
        st.dataframe(summary.sort_values('month', ascending=False))
        # chart
        fig = px.bar(summary, x='month', y=['income','expenses'], title="Income vs Expenses by Month")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No income/expense data yet.")

# -------------------- EXPENSE REPORTS & CHARTS --------------------
elif menu == "Expense Reports & Charts":
    st.header("📈 Expense Reports & Charts")
    st.subheader("Expenses by Vehicle (date range)")
    start_date = st.date_input("Start date", datetime.now() - timedelta(days=60), key="rep_start")
    end_date = st.date_input("End date", datetime.now(), key="rep_end")
    if start_date > end_date:
        st.error("Start date > end date.")
    else:
        q = """SELECT vehicle_no, SUM(petrol) AS petrol, SUM(toll) AS toll,
               SUM(maintenance) AS maintenance, SUM(tips) AS tips,
               SUM(petrol + toll + maintenance + tips) AS total
               FROM expenses WHERE date BETWEEN ? AND ? GROUP BY vehicle_no"""
        df = query_df(q, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        if df.empty:
            st.info("No expense data for this period.")
        else:
            st.dataframe(df)
            fig = px.bar(df.sort_values('total', ascending=False), x='vehicle_no', y=['petrol','toll','maintenance','tips'],
                         title=f"Expenses per Vehicle ({start_date} to {end_date})", barmode='stack')
            st.plotly_chart(fig, use_container_width=True)

# -------------------- INSURANCE & ALERTS --------------------
elif menu == "Insurance & Alerts":
    st.header("🛡️ Insurance & Alerts")
    st.subheader("Set / Update Insurance for Vehicles")
    with st.form("ins_form"):
        vehicles = query_df("SELECT vehicle_no FROM vehicles")
        opts = vehicles['vehicle_no'].tolist() if not vehicles.empty else []
        v = st.selectbox("Vehicle", opts) if opts else st.text_input("Vehicle No")
        ins_date = st.date_input("Insurance expiry date", value=datetime.now() + timedelta(days=365))
        submitted = st.form_submit_button("Update Insurance")
        if submitted:
            if opts:
                execute("UPDATE vehicles SET insurance_expiry=? WHERE vehicle_no=?", (ins_date.strftime("%Y-%m-%d"), v))
            else:
                st.warning("Add vehicles first via Vehicle Management.")
            st.success("Insurance updated.")
    st.markdown("---")
    st.subheader("Upcoming Insurance Expiries (next 30 days)")
    df = query_df("SELECT vehicle_no, model, insurance_expiry FROM vehicles WHERE insurance_expiry IS NOT NULL AND insurance_expiry != '' AND date(insurance_expiry) <= date(?) ORDER BY insurance_expiry",
                  ((datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d"),))
    if df.empty:
        st.success("No expiries in the next 30 days.")
    else:
        st.table(df)

# -------------------- PENDING TASKS --------------------
elif menu == "Pending Tasks":
    st.header("📝 Pending Tasks / Work")
    with st.expander("Add Task"):
        with st.form("task_form"):
            vehicles = query_df("SELECT vehicle_no FROM vehicles")
            opts = vehicles['vehicle_no'].tolist() if not vehicles.empty else []
            v = st.selectbox("Vehicle", opts) if opts else st.text_input("Vehicle No")
            desc = st.text_input("Description")
            due = st.date_input("Due date", value=datetime.now()+timedelta(days=7))
            submitted = st.form_submit_button("Add Task")
            if submitted:
                add_task(v, desc, due.strftime("%Y-%m-%d"))
                st.success("Task added.")
    st.markdown("---")
    st.subheader("Current Tasks")
    tasks_df = query_df("SELECT * FROM tasks ORDER BY due_date")
    st.dataframe(tasks_df)

# -------------------- EXPORT DATA --------------------
elif menu == "Export Data":
    st.header("⬇️ Export / Download Data")
    if st.button("Export drivers.csv"):
        df = query_df("SELECT * FROM drivers")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download drivers.csv", csv, "drivers.csv", "text/csv")
    if st.button("Export expenses.csv"):
        df = query_df("SELECT * FROM expenses")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download expenses.csv", csv, "expenses.csv", "text/csv")
    if st.button("Export income.csv"):
        df = query_df("SELECT * FROM income")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download income.csv", csv, "income.csv", "text/csv")
    st.markdown("You can also copy/paste tables shown elsewhere.")

# -------------------- LOGOUT --------------------
elif menu == "Logout":
    st.session_state.logged_in = False
    st.success("Logged out.")
    st.rerun()
