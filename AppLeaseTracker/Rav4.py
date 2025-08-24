import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import date, datetime, timedelta

# -----------------------------
# App setup (always dark)
# -----------------------------
st.set_page_config(page_title="מנהל קילומטראז' ליסינג", layout="wide")
st.title("🚗 מנהל קילומטראז' לליסינג")

# Force dark theme + RTL CSS
DARK_CSS = """
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
  --accent-1: #22d3ee;
  --accent-2: #a3e635;
  --danger: #ef4444;
}
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg);
  color: var(--text);
  direction: rtl;
  text-align: right;
}
[data-testid="stHeader"]{ background: transparent; }
body, .stMarkdown, .stText, .stAlert { font-size: 16px; line-height: 1.55; }
h1, .stTitle { font-size: 28px !important; }
h2 { font-size: 22px !important; }
[data-testid="stExpander"] > div { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }
summary { color: var(--text); font-weight: 600; }
label { color: var(--text) !important; font-weight: 600; }
.stTextInput input, .stNumberInput input, .stDateInput input { background: var(--panel-2); color: var(--text); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; text-align: right; }
.stButton>button { background: var(--primary); color: #fff; border: 1px solid var(--primary); border-radius: 12px; font-weight: 700; padding: 10px 14px; }
.stButton>button:hover { background: var(--primary-hover); border-color: var(--primary-hover); }
div[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 12px 14px; text-align: right; }
div[data-testid="stMetric"] [data-testid="stMetricLabel"] { color: var(--muted); font-size: 14px; font-weight:600; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--text); font-size: 24px; font-weight: 800; }
div[data-testid="stMetric"] [data-testid="stMetricDelta"] { font-size: 16px; font-weight:700; }
.stDataFrame { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; direction: rtl; }
div[data-testid="stSidebar"] { background: var(--panel); color: var(--text); border-left: 1px solid var(--border); direction: rtl; text-align: right; }
a { color: var(--primary); }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# -----------------------------
# Defaults & DB
# -----------------------------
DEFAULT_START_DATE = date(2025, 4, 20)
DEFAULT_TERM_YEARS = 3
DEFAULT_ANNUAL_CAP = 20_000
DEFAULT_PENALTY_PER_KM = 1.18
# DB_PATH = "lease_tracker.db"

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "lease_tracker.db")


@st.cache_resource
def get_conn(db_path: str):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS readings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_date TEXT NOT NULL,
            odometer INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    return conn

conn = get_conn(DB_PATH)

@st.cache_data(ttl=1)
def load_readings(_conn):
    df = pd.read_sql_query(
        "SELECT id, reading_date, odometer FROM readings ORDER BY reading_date ASC, id ASC",
        _conn,
    )
    if not df.empty:
        df["reading_date"] = pd.to_datetime(df["reading_date"]).dt.date
    return df

def add_reading(_conn, when: date, odo: int):
    _conn.execute("INSERT INTO readings(reading_date, odometer) VALUES(?, ?)", (when.isoformat(), int(odo)))
    _conn.commit()

# -----------------------------
# Contract settings
# -----------------------------
with st.expander("⚙️ הגדרות ליסינג", expanded=True):
    col1, col2, col3 = st.columns([1.2,1,1])
    with col1:
        start_date = st.date_input("תאריך התחלה", value=DEFAULT_START_DATE, format="DD/MM/YYYY")
        start_odometer = st.number_input('ק"מ בתחילת החוזה', min_value=0, value=0, step=100)
    with col2:
        term_years = st.number_input("משך (שנים)", min_value=1, max_value=6, value=DEFAULT_TERM_YEARS, step=1)
        annual_cap = st.number_input('מכסה שנתית [ק"מ]', min_value=5_000, max_value=100_000, value=DEFAULT_ANNUAL_CAP, step=1_000)
    with col3:
        penalty_per_km = st.number_input('קנס לק"מ חריגה [₪]', min_value=0.0, value=DEFAULT_PENALTY_PER_KM, step=0.01, format="%.2f")

# -----------------------------
# Calculations (daily cap based on chosen annual cap)
# -----------------------------
end_date = date(start_date.year + term_years, start_date.month, start_date.day)
lease_total_days = (end_date - start_date).days + 1
fixed_daily_cap = annual_cap / 365.0

# -----------------------------
# Input: add a reading
# -----------------------------
with st.expander('הזנת קריאה (ק"מ נוכחי)', expanded=True):
    c1, c2, c3 = st.columns([1.2, 1, 1])
    reading_date = c1.date_input("תאריך הקריאה", value=date.today(), format="DD/MM/YYYY", min_value=start_date, max_value=end_date)
    odometer_now = c2.number_input('ק"מ נוכחי', min_value=0, step=10)
    if c3.button("➕ הוסף קריאה", use_container_width=True):
        readings_now = load_readings(conn)
        if not readings_now.empty and int(odometer_now) < int(readings_now["odometer"].iloc[-1]):
            st.error("ערך הק""מ קטן מהקריאה האחרונה. אנא הזן ערך גדול או שווה.")
        else:
            add_reading(conn, reading_date, int(odometer_now))
            st.success("נשמר!")
            st.cache_data.clear()

readings = load_readings(conn)
last_odo = int(readings["odometer"].iloc[-1]) if not readings.empty else None

as_of = date.today()
elapsed_days_inc = min((as_of - start_date).days + 1, lease_total_days) if as_of >= start_date else 0
remaining_days_inc = max(0, lease_total_days - elapsed_days_inc)

allowed_to_date = round(elapsed_days_inc * fixed_daily_cap, 2)
used_km = max(0, (last_odo - start_odometer) if (last_odo is not None) else 0)
delta_vs_allowed = round(used_km - allowed_to_date, 2)

avg_per_day = round((used_km / elapsed_days_inc), 2) if elapsed_days_inc > 0 else 0.0
projected_total = round(avg_per_day * lease_total_days, 2)
total_cap = round(fixed_daily_cap * lease_total_days, 2)
projected_overage = max(0, projected_total - total_cap)
projected_penalty = round(projected_overage * penalty_per_km, 2)
needed_per_day = round(((total_cap - used_km) / remaining_days_inc), 2) if remaining_days_inc > 0 else 0.0

# -----------------------------
# KPIs
# -----------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("תחילת חוזה", start_date.strftime("%d/%m/%Y"))
k2.metric("סיום חוזה", end_date.strftime("%d/%m/%Y"))
k3.metric("ימי חוזה", f"{lease_total_days:,}")
percent_elapsed = round(100.0 * (elapsed_days_inc / lease_total_days), 2) if lease_total_days else 0.0
k4.metric("ימים שחלפו", f"{elapsed_days_inc:,}", delta=f"{percent_elapsed:.2f}% מהתקופה")

k5, k6, k7 = st.columns(3)
k5.metric('מכסה יומית קבועה', f"{fixed_daily_cap:.2f} ק""מ/יום")
k6.metric('מותר עד היום', f"{int(allowed_to_date):,} ק""מ", delta=f"{delta_vs_allowed:+,.2f} ק""מ מול בפועל")
k7.metric('נצרך עד כה', f"{used_km:,} ק""מ")

k8, k9, k10 = st.columns(3)
k8.metric('קצב יומי נוכחי', f"{avg_per_day:.2f} ק""מ/יום")
k9.metric('דרוש מעכשיו', f"{needed_per_day:.2f} ק""מ/יום")
k10.metric('חריגה חזויה', f"{projected_overage:,.2f} ק""מ", delta=f"Penalty ₪{projected_penalty:,.2f}")

# -----------------------------
# Chart
# -----------------------------
with st.expander("Progress Chart", expanded=True):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.patch.set_facecolor('#0b0f14')
    ax.set_facecolor('#0b0f14')
    grid_color = '#334155'
    label_color = '#e5e7eb'
    allowed_color = '#22d3ee'
    actual_color = '#a3e635'

    for spine in ax.spines.values():
        spine.set_color(label_color)
    ax.tick_params(colors=label_color, labelsize=11)

    days_axis = np.arange(0, lease_total_days)
    allowed_curve = days_axis * fixed_daily_cap
    dates_axis = [start_date + timedelta(days=int(d)) for d in days_axis]

    ax.plot(dates_axis, allowed_curve, label="Allowed (target)", linewidth=2.5, color=allowed_color)

    if not readings.empty:
        df_plot = readings.copy()
        df_plot["used_from_start"] = df_plot["odometer"].astype(int) - int(start_odometer)
        df_plot.loc[df_plot["used_from_start"] < 0, "used_from_start"] = 0
        ax.plot(df_plot["reading_date"], df_plot["used_from_start"], marker="o", markersize=5, linewidth=2.2, label="Actual", color=actual_color)

    ax.axvline(as_of, linestyle='--', linewidth=1.5, color=grid_color, label='Today')

    ax.set_xlabel("תאריך", color=label_color, fontsize=12)
    ax.set_ylabel("ק""מ מצטבר", color=label_color, fontsize=12)
    ax.grid(True, alpha=0.45, color=grid_color)
    leg = ax.legend(facecolor='none', edgecolor='none', fontsize=11)
    for text in leg.get_texts():
        text.set_color(label_color)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
