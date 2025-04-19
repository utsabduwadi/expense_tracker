import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import hashlib
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os

# Database setup
def init_db():
    conn = sqlite3.connect('./data/expense_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        name TEXT,
        email TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        username TEXT,
        category TEXT,
        PRIMARY KEY (username, category)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        amount REAL,
        category TEXT,
        date TEXT,
        description TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        item TEXT,
        purchased INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
        username TEXT,
        year INTEGER,
        month INTEGER,
        goal_amount REAL,
        PRIMARY KEY (username, year, month)
    )''')
    conn.commit()
    conn.close()

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication
def authenticate(username, password):
    conn = sqlite3.connect('./data/expense_tracker.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == hash_password(password):
        return True
    return False

# Add user with default categories
def add_user(username, password, name, email):
    conn = sqlite3.connect('./data/expense_tracker.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, name, email) VALUES (?, ?, ?, ?)",
                    (username, hash_password(password), name, email))
        default_categories = ['Food', 'Transport', 'Education', 'Rent', 'Entertainment', 'Others']
        for category in default_categories:
            c.execute("INSERT OR IGNORE INTO categories (username, category) VALUES (?, ?)",
                        (username, category))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Main app
def main():
    st.set_page_config(page_title="Expense Tracker", layout="wide")
    init_db()

    # Asset paths (replaced with emojis and Streamlit elements)
    ASSET_PATHS = {
        'logo': '💰',  # Using a money bag emoji as a simple logo
        'login_bg': '👤🔑', # User and key emojis for login
        'signup_bg': '📝✨', # Writing hand and sparkles for signup
        'dashboard_icon': '📊',
        'add_expense_icon': '➕💸',
        'wishlist_icon': '📋',
        'categories_icon': '🗂️',
        'set_goal_icon': '🎯',
        'reports_icon': '📈',
        'logout_icon': '🚪',
        'login_icon': '➡️',
        'signup_icon': '✍️',
        'spending_icon': '📉',
        'reports_header': '📰',
        'category_icons': {
            'Food': '🍽️',
            'Transport': '🚗',
            'Education': '📚',
            'Rent': '🏠',
            'Entertainment': '🎬',
            'Others': '❓'
        }
    }

    # Session state for login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = "Login"

    # Sidebar navigation with icons
    with st.sidebar:
        st.header(f"{ASSET_PATHS['logo']} Expense Tracker")
        if st.session_state.logged_in:
            st.write(f"👋 Welcome, {st.session_state.username}!")
            for label, icon_key in [
                ("Dashboard", "dashboard_icon"),
                ("Add Expense", "add_expense_icon"),
                ("Wishlist", "wishlist_icon"),
                ("Categories", "categories_icon"),
                ("Set Goal", "set_goal_icon"),
                ("Reports", "reports_icon"),
                ("Logout", "logout_icon")
            ]:
                icon = ASSET_PATHS[icon_key]
                if st.button(f"{icon} {label}", key=f"{label.lower().replace(' ', '_')}_button"):
                    st.session_state.page = label
                    if label == "Logout":
                        st.session_state.confirm_logout = True
            if 'confirm_logout' in st.session_state and st.session_state.confirm_logout:
                st.warning("Are you sure you want to log out?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Confirm", key="confirm_logout_button"):
                        st.session_state.logged_in = False
                        st.session_state.username = None
                        st.session_state.page = "Login"
                        st.session_state.confirm_logout = False
                        st.success("Logged out successfully!")
                        st.rerun()
                with col2:
                    if st.button("Cancel", key="cancel_logout_button"):
                        st.session_state.confirm_logout = False
                        st.rerun()
        else:
            for label, icon_key in [("Login", "login_icon"), ("Sign Up", "signup_icon")]:
                icon = ASSET_PATHS[icon_key]
                if st.button(f"{icon} {label}", key=f"{label.lower().replace(' ', '_')}_nav_button"):
                    st.session_state.page = label

    # Login/Signup
    if not st.session_state.logged_in:
        if st.session_state.page == "Login":
            st.markdown(f'<div style="font-size:2em; margin-bottom:20px;">{ASSET_PATHS["login_bg"]}</div>', unsafe_allow_html=True)
            st.header("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_submit_button"):
                if authenticate(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.page = "Dashboard"
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        elif st.session_state.page == "Sign Up":
            st.markdown(f'<div style="font-size:2em; margin-bottom:20px;">{ASSET_PATHS["signup_bg"]}</div>', unsafe_allow_html=True)
            st.header("Sign Up")
            username = st.text_input("Username", key="signup_username")
            password = st.text_input("Password", type="password", key="signup_password")
            name = st.text_input("Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            if st.button("Sign Up", key="signup_submit_button"):
                if add_user(username, password, name, email):
                    st.success("Account created! Please log in.")
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    st.error("Username already exists")
        return

    # Logged-in features
    conn = sqlite3.connect('./data/expense_tracker.db')
    username = st.session_state.username
    c = conn.cursor()

    if st.session_state.page == "Dashboard":
        st.header(f"{ASSET_PATHS['dashboard_icon']} Dashboard")
        # Goal and Spending Section
        st.subheader(f"{ASSET_PATHS['spending_icon']} Spending & Goal")
        current_year, current_month = date.today().year, date.today().month
        c.execute("SELECT goal_amount FROM goals WHERE username = ? AND year = ? AND month = ?",
                    (username, current_year, current_month))
        goal_result = c.fetchone()
        goal_amount = goal_result[0] if goal_result else 0.0
        df = pd.read_sql_query(
            "SELECT * FROM expenses WHERE username = ? AND strftime('%Y-%m', date) = ?",
            conn, params=(username, f"{current_year}-{current_month:02d}")
        )
        total_expense = df['amount'].sum() if not df.empty else 0.0

        progress_color = "#4CAF50"  # Green for on track
        progress_text = "✅ On track with your goal!"
        progress_percent = 0.0
        if goal_amount > 0:
            progress_percent = min(total_expense / goal_amount, 1.0)
            if progress_percent > 0.8:
                progress_color = "#FF9800"  # Orange for nearing limit
            if progress_percent > 1.0:
                progress_color = "#F44336"  # Red for overspent
                progress_text = "😔 You have overspent!"
            st.metric("Monthly Spending", f"${total_expense:.2f} / ${goal_amount:.2f}",
                        delta=f"{progress_percent*100:.1f}% of Goal")
        else:
            st.metric("Monthly Spending", f"${total_expense:.2f}", delta="No goal set")
            st.warning("No goal set for this month.")

        # Colorful progress bar using HTML
        progress_bar_html = f"""
            <div style="background-color:#f0f2f6; border-radius: 5px; height: 10px; width: 100%;">
                <div style="background-color:{progress_color}; border-radius: 5px; height: 10px; width: {progress_percent * 100}%;"></div>
            </div>
            """
        st.markdown(progress_bar_html, unsafe_allow_html=True)
        st.markdown(f"<span style='color:{progress_color};'>{progress_text}</span>", unsafe_allow_html=True)

        if goal_amount == 0 and st.button("Set Goal Now", key="dashboard_set_goal_button"):
            st.session_state.page = "Set Goal"
            st.rerun()

        # Date picker for charts
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today(), key="dashboard_start_date")
        with col2:
            end_date = st.date_input("End Date", value=date.today(), key="dashboard_end_date")

        df = pd.read_sql_query(
            "SELECT * FROM expenses WHERE username = ? AND date BETWEEN ? AND ?",
            conn, params=(username, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        )

        # Initialize charts with all categories
        c.execute("SELECT category FROM categories WHERE username = ?", (username,))
        categories = [row[0] for row in c.fetchall()]
        category_df = pd.DataFrame({'category': categories, 'amount': [0]*len(categories)})
        category_summary = df.groupby('category')['amount'].sum().reset_index()
        if not category_summary.empty:
            category_df = category_df.merge(category_summary, on='category', how='left')
            category_df['amount'] = category_df['amount_y'].fillna(category_df['amount_x'])
            category_df = category_df[['category', 'amount']]

        # Bar Graph with category icons
        st.subheader(f"{ASSET_PATHS['dashboard_icon']} Expenses by Categories")
        for _, row in category_df.iterrows():
            category = row['category']
            icon = ASSET_PATHS['category_icons'].get(category, ASSET_PATHS['category_icons']['Others'])
            st.markdown(f'<span style="font-size:16px; vertical-align:middle; margin-right:5px;">{icon}</span> {category}: ${row["amount"]:.2f}', unsafe_allow_html=True)
        fig_bar = px.bar(category_df, x='category', y='amount', title="",
                            color='category', color_discrete_sequence=px.colors.qualitative.Plotly)
        fig_bar.update_layout(showlegend=False, xaxis_title="Category", yaxis_title="Amount ($)")
        st.plotly_chart(fig_bar)

        # Pie Chart
        st.subheader("Category Distribution")
        if category_summary.empty:
            st.info("No expenses recorded for this period. Add expenses to see distribution.")
        else:
            fig_pie = px.pie(category_summary, names='category', values='amount', title="",
                                color_discrete_sequence=px.colors.qualitative.Plotly)
            st.plotly_chart(fig_pie)

        # Additional Metrics
        if not df.empty:
            highest = df.loc[df['amount'].idxmax()]
            lowest = df.loc[df['amount'].idxmin()]
            st.write(f"**Highest Expense**: ${highest['amount']:.2f} on {highest['date']} ({highest['category']})")
            st.write(f"**Lowest Expense**: ${lowest['amount']:.2f} on {highest['date']} ({highest['category']})")

    elif st.session_state.page == "Add Expense":
        st.header(f"{ASSET_PATHS['add_expense_icon']} Add Expense")
        c.execute("SELECT category FROM categories WHERE username = ?", (username,))
        categories = [row[0] for row in c.fetchall()]
        if not categories:
            st.warning("No categories found. Please add categories first.")
            return

        amount = st.number_input("Amount", min_value=0.0, step=0.01, key="expense_amount")
        category = st.selectbox("Category", categories, key="expense_category")
        date_input = st.date_input("Date", value=date.today(), key="expense_date")
        description = st.text_input("Description", key="expense_description")
        check_wishlist = st.checkbox("Check Wishlist", key="expense_wishlist_check")

        if st.button("Add Expense", key="add_expense_submit_button"):
            if check_wishlist and description:
                c.execute("SELECT item, purchased FROM wishlist WHERE username = ? AND purchased = 0", (username,))
                wishlist_items = [row[0] for row in c.fetchall()]
                if description not in wishlist_items:
                    st.warning("This item is not on your wishlist. Are you sure you want to add it?")
                    if st.button("Confirm Add", key="confirm_add_expense_button"):
                        c.execute("INSERT INTO expenses (username, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                                    (username, amount, category, date_input.strftime('%Y-%m-%d'), description))
                        conn.commit()
                        st.success("Expense added!")
                else:
                    c.execute("INSERT INTO expenses (username, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                                (username, amount, category, date_input.strftime('%Y-%m-%d'), description))
                    c.execute("UPDATE wishlist SET purchased = 1 WHERE username = ? AND item = ?", (username, description))
                    conn.commit()
                    st.success("Expense added and wishlist item marked as purchased!")
            elif description:
                c.execute("INSERT INTO expenses (username, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                            (username, amount, category, date_input.strftime('%Y-%m-%d'), description))
                conn.commit()
                st.success("Expense added!")
            else:
                st.error("Please enter a description.")

    elif st.session_state.page == "Wishlist":
        st.header(f"{ASSET_PATHS['wishlist_icon']} Wishlist")
        item = st.text_input("Add Item to Wishlist", key="wishlist_item")
        if st.button("Add to Wishlist", key="add_wishlist_button"):
            if item:
                c.execute("INSERT INTO wishlist (username, item, purchased) VALUES (?, ?, 0)", (username, item))
                conn.commit()
                st.success(f"Added {item} to wishlist")
            else:
                st.error("Please enter an item name.")

        c.execute("SELECT item, purchased FROM wishlist WHERE username = ?", (username,))
        wishlist = c.fetchall()
        if wishlist:
            st.subheader("Your Wishlist:")
            for item, purchased in wishlist:
                status = "✅ Purchased" if purchased else "⬜ Pending"
                st.write(f"- {item} ({status})")
        else:
            st.info("Your wishlist is empty.")

    elif st.session_state.page == "Categories":
        st.header(f"{ASSET_PATHS['categories_icon']} Manage Categories")
        new_category = st.text_input("New Category", key="category_input")
        if st.button("Add Category", key="add_category_button"):
            if new_category:
                try:
                    c.execute("INSERT INTO categories (username, category) VALUES (?, ?)", (username, new_category))
                    conn.commit()
                    st.success(f"Added category: {new_category}")
                except sqlite3.IntegrityError:
                    st.error("Category already exists")
            else:
                st.error("Please enter a category name.")

        c.execute("SELECT category FROM categories WHERE username = ?", (username,))
        categories = [row[0] for row in c.fetchall()]
        if categories:
            st.subheader("Current Categories:")
            st.write(", ".join(categories))
        else:
            st.info("No categories added yet.")

    elif st.session_state.page == "Set Goal":
        st.header(f"{ASSET_PATHS['set_goal_icon']} Set Monthly Goal")
        year = st.number_input("Year", min_value=2020, max_value=2100, value=date.today().year, key="goal_year")
        month = st.selectbox("Month", range(1, 13), index=date.today().month-1, key="goal_month")
        goal_amount = st.number_input("Goal Amount ($)", min_value=0.0, step=10.0, key="goal_amount")
        if st.button("Set Goal", key="set_goal_submit_button"):
            if goal_amount > 0:
                c.execute("INSERT OR REPLACE INTO goals (username, year, month, goal_amount) VALUES (?, ?, ?, ?)",
                            (username, year, month, goal_amount))
                conn.commit()
                st.success(f"Goal set: ${goal_amount} for {month}/{year}")
            else:
                st.error("Please enter a valid goal amount.")

    elif st.session_state.page == "Reports":
        st.markdown(f'<div style="font-size:1.5em; margin-bottom:20px;">{ASSET_PATHS["reports_header"]}</div>', unsafe_allow_html=True)
        st.header("Reports")
        st.subheader(f"{ASSET_PATHS['spending_icon']} Spending & Goal Summary")
        current_year, current_month = date.today().year, date.today().month
        c.execute("SELECT goal_amount FROM goals WHERE username = ? AND year = ? AND month = ?",
                    (username, current_year, current_month))
        goal_result = c.fetchone()
        goal_amount = goal_result[0] if goal_result else 0.0
        df = pd.read_sql_query(
            "SELECT * FROM expenses WHERE username = ? AND strftime('%Y-%m', date) = ?",
            conn, params=(username, f"{current_year}-{current_month:02d}")
        )
        total_expense = df['amount'].sum() if not df.empty else 0.0

        progress_color_report = "#4CAF50"  # Default green
        spending_status_report = "within budget"
        if goal_amount > 0:
            progress_report = total_expense / goal_amount
            if progress_report > 0.8:
                progress_color_report = "#FF9800"
                spending_status_report = "nearing limit"
            if progress_report > 1.0:
                progress_color_report = "#F44336"
                spending_status_report = "overspent"

        if goal_amount > 0:
            st.metric("Monthly Spending", f"${total_expense:.2f} / ${goal_amount:.2f}",
                        delta=f"{progress_report*100:.1f}% of Goal")
            st.markdown(f"<span style='color:{progress_color_report};'>Spending status: {spending_status_report.capitalize()}</span>", unsafe_allow_html=True)
        else:
            st.metric("Monthly Spending", f"${total_expense:.2f}", delta="No goal set")
            st.warning("No goal set for this month.")

        st.subheader("Expense Breakdown")
        category_summary = df.groupby('category')['amount'].sum().reset_index() if not df.empty else pd.DataFrame(columns=['category', 'amount'])
        if not category_summary.empty:
            fig_bar = px.bar(category_summary, x='category', y='amount', title="Expenses by Category",
                                color='category', color_discrete_sequence=px.colors.qualitative.Plotly)
            st.plotly_chart(fig_bar)
        else:
            st.info("No expenses recorded for this month.")

        st.subheader("All Expenses")
        if not df.empty:
            st.dataframe(df[['date', 'category', 'amount', 'description']])
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "expenses.csv", "text/csv", key="download_csv_button")
            if st.button("Generate Monthly PDF", key="generate_pdf_button"):
                monthly_df = df
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                c.drawString(100, 750, f"Monthly Report: {current_month}/{current_year}")
                c.drawString(100, 730, f"Total Spending: ${total_expense:.2f}")
                c.drawString(100, 710, f"Goal: ${goal_amount if goal_amount > 0 else 0:.2f}")
                c.drawString(100, 690, f"Spending Status: {spending_status_report.capitalize()}")
                y = 660
                for _, row in monthly_df.iterrows():
                    c.drawString(100, y, f"{row['date']} | {row['category']} | ${row['amount']:.2f} | {row['description']}")
                    y -= 20
                    if y < 50:
                        c.showPage()
                        y = 750
                c.showPage()
                c.save()
                buffer.seek(0)
                st.download_button("Download PDF", buffer, f"report_{current_year}_{current_month}.pdf",
                                    "application/pdf", key="download_pdf_button")
        else:
            st.info("No expenses recorded yet.")

    conn.close()

if __name__ == "__main__":
    main()