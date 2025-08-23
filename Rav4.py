import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import date, datetime, timedelta

# -----------------------------
# הגדרות ראשוניות
# -----------------------------
st.set_page_config(page_title="מנהל קילומטראז' ליסינג", layout="wide")
st.title("🚗 מנהל קילומטראז' לליסינג")

# Always Dark Mode CSS
theme_css = """
<style>
:root {
  --bg: #0b0f14;
  --panel: #111827;
  --panel-2: #0f172a;
  --text: #f3f4f6;
  --muted: #cbd5e1;
  --border: #334155;
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --accent: #9333ea;
}
</style>
"""

st.markdown(theme_css, unsafe_allow_html=True)

# -----------------------------
# Database setup
# -----------------------------
DB_FILE = "lease_tracker.db"

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    odometer INTEGER NOT NULL
)
""")
conn.commit()

# -----------------------------
# פונקציות עזר
# -----------------------------
def add_reading(reading_date, odometer):
    c.execute("INSERT INTO readings (date, odometer) VALUES (?, ?)", (reading_date, odometer))
    conn.commit()

def get_readings():
    c.execute("SELECT * FROM readings ORDER BY date")
    rows = c.fetchall()
    return pd.DataFrame(rows, columns=["id", "date", "odometer"])

# -----------------------------
# טופס הגדרות חוזה
# -----------------------------
st.sidebar.markdown("### ⚙️ הגדרות חוזה")
annual_cap = st.sidebar.number_input("מכסה שנתית (ק""מ)", min_value=5000, max_value=50000, value=20000, step=1000)
term_years = st.sidebar.number_input("מספר שנות חוזה", min_value=1, max_value=5, value=3, step=1)

# חישוב מכסה יומית לפי ההגדרה של המשתמש
daily_cap = annual_cap / 365.0

# -----------------------------
# טופס הוספת קריאה
# -----------------------------
st.sidebar.markdown("### ➕ הוספת קריאת מד ק""מ")
with st.sidebar.form("reading_form"):
    reading_date = st.date_input("תאריך", value=date.today())
    odometer = st.number_input("מד ק""מ", min_value=0, step=1)
    submitted = st.form_submit_button("הוסף קריאה")
    if submitted:
        add_reading(str(reading_date), odometer)
        st.success("הקריאה נוספה בהצלחה!")

# -----------------------------
# הצגת קריאות
# -----------------------------
readings_df = get_readings()
if readings_df.empty:
    st.info("לא קיימות קריאות במערכת. הוסף קריאה ראשונה בסרגל הצד.")
else:
    st.subheader("📊 קריאות שנרשמו")
    st.dataframe(readings_df)

    # גרף קילומטראז'
    st.subheader("📈 גרף ק""מ מצטבר")
    fig, ax = plt.subplots()
    ax.plot(pd.to_datetime(readings_df["date"]), readings_df["odometer"], marker="o")
    ax.set_xlabel("תאריך")
    ax.set_ylabel("ק""מ")
    ax.grid(True)
    st.pyplot(fig)

    # הצגת מכסה יומית
    st.sidebar.markdown(f"מכסה יומית: {daily_cap:.1f} ק""מ")
