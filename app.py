import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")

# רשימת ליקויים (ישראל/ירושלים) עם שעות מקסימום מקומיות
# מקורות: timeanddate.com ו-TheSkyLive (מצוינים למטה)
ECLIPSES = [
    # (תאריך-שיא, סוג, גוף, תיאור קצר, שעת התחלה/מקסימום/סיום אם רלוונטי)
    # ליקויי ירח
    {
        "date": datetime(2025, 3, 14, 2, 58, tzinfo=TZ),
        "kind": "Total",
        "body": "Lunar",
        "label": "ליקוי ירח מלא",
        "notes": "שיא בלילה שבין 13–14 במרץ (02:58)",
    },
    {
        "date": datetime(2025, 9, 7, 21, 12, tzinfo=TZ),
        "kind": "Total",
        "body": "Lunar",
        "label": "ליקוי ירח מלא",
        "notes": "ירח זורח לתוך הליקוי; שיא ~21:12",
    },
    {
        "date": datetime(2026, 8, 28, 6, 10, tzinfo=TZ),
        "kind": "Partial",
        "body": "Lunar",
        "label": "ליקוי ירח חלקי",
        "notes": "שיא סמוך לשקיעה; התחלה 04:23, שיא 06:10, סוף 06:13",
    },
    {
        "date": datetime(2027, 2, 20, 18, 16, tzinfo=TZ),
        "kind": "Penumbral",
        "body": "Lunar",
        "label": "ליקוי ירח במעבר חצי־צל",
        "notes": "שיא ~18:16; קושי תצפית בגלל גובה נמוך",
    },
    {
        "date": datetime(2028, 1, 12, 6, 13, tzinfo=TZ),
        "kind": "Partial",
        "body": "Lunar",
        "label": "ליקוי ירח חלקי",
        "notes": "שיא ~06:13, הירח ישקע לפני סיום האירוע",
    },

    # ליקויי חמה (בישראל: מקומי = חלקי, גלובלי עשוי להיות מלא/טבעתי)
    {
        "date": datetime(2027, 8, 2, 13, 1, tzinfo=TZ),
        "kind": "Partial (local)",
        "body": "Solar",
        "label": "ליקוי חמה חלקי (בישראל) / גלובלי: מלא",
        "notes": "התחלה 11:40, שיא 13:01, סוף 14:18 (ירושלים)",
    },
    # אפשר להרחיב בהמשך (2030 ועוד) לפי צורך
]

st.set_page_config(page_title="Eclipse Finder – Israel", layout="centered")

st.title("ליקויי ירח וחמה הקרובים – ישראל")
st.caption("התאריכים והשעות מוצגים לפי אזור זמן Asia/Jerusalem.")

# מיון ובקרת אינדקס לדפדוף
ECLIPSES.sort(key=lambda e: e["date"])

if "idx" not in st.session_state:
    # קבע אינדקס התחלתי לאירוע הבא (>= עכשיו), ואם אין – לאחרון
    now = datetime.now(TZ)
    next_idx = 0
    for i, ev in enumerate(ECLIPSES):
        if ev["date"] >= now:
            next_idx = i
            break
    st.session_state.idx = next_idx

col_prev, col_now, col_next = st.columns([1,2,1])
with col_prev:
    if st.button("◀︎ prev"):
        st.session_state.idx = max(0, st.session_state.idx - 1)
with col_next:
    if st.button("next ▶︎"):
        st.session_state.idx = min(len(ECLIPSES)-1, st.session_state.idx + 1)

ev = ECLIPSES[st.session_state.idx]

st.subheader(f"{ev['label']} — {ev['date'].strftime('%A, %d %B %Y')}")
st.write(
    f"**סוג/מצב:** {ev['kind']} {ev['body']}  \n"
    f"**שעת שיא מקומית:** {ev['date'].strftime('%H:%M')}  \n"
    f"**הערות:** {ev['notes']}"
)

# תיבה עם רשימת כל האירועים לדילוג מהיר
with st.expander("דלג ישירות לאירוע אחר"):
    for i, e in enumerate(ECLIPSES):
        label = f"{e['date'].strftime('%Y-%m-%d %H:%M')} – {e['label']}"
        if st.button(label, key=f"jump_{i}"):
            st.session_state.idx = i
            st.rerun()

st.info(
    "זכור: ליקוי *חמה* מוצג כאן לפי הנראות בישראל (לרוב חלקי), "
    "גם אם גלובלית הוא מלא/טבעתי."
)
