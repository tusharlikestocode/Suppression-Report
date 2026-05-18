import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(layout="wide")

# --- REMOVE EXTRA PADDING ---
st.markdown("""
<style>
/* Background */
body {
    background-color: #0E1117;
}

/* Metric Cards */
[data-testid="metric-container"] {
    background-color: #1c1f26;
    border: 1px solid #2e3440;
    padding: 10px;
    border-radius: 10px;
}

/* Titles */
h1, h2, h3 {
    color: #EAEAEA;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: #1c1f26;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Suppression Dashboard")
def highlight_category(val):
    if "Space Out" in str(val):
        return "background-color: #1f7a63; color: white"
    else:
        return "background-color: #7a2f2f; color: white"
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # --- CLEANING ---
    df['NEXT_BILLING_DATE'] = pd.to_datetime(df['NEXT_BILLING_DATE'], errors='coerce')
    today = datetime.today()

    df = df[df['NEXT_BILLING_DATE'].dt.year >= 2026]
    df = df[
        (df['NEXT_BILLING_DATE'].dt.year < today.year) |
        (
            (df['NEXT_BILLING_DATE'].dt.year == today.year) &
            (df['NEXT_BILLING_DATE'].dt.month <= today.month)
        )
    ]

    df = df.sort_values(by='NEXT_BILLING_DATE', ascending=False)
    df = df.drop_duplicates(subset=['ACCOUNT_NO'], keep='first')
    df = df[~df['NOTE_TEXT'].str.lower().str.contains('dummy', na=False)]

    # --- CATEGORY ---
    def categorize(note):
        note = str(note).lower()
        if "space out" in note:
            return "Space Out"
        elif "adj" in note:
            return "Biz planned suppression (pending Adjustment)"
        elif "pending order" in note:
            return "Biz planned suppression (pending order)"
        else:
            return "Biz planned suppression"

    df['category'] = df['NOTE_TEXT'].apply(categorize)
    df['month'] = df['NEXT_BILLING_DATE'].dt.strftime('%b %Y')

    # --- METRICS ---
    grand_total = len(df)

    df['days_on_hold'] = (pd.to_datetime(today) - df['NEXT_BILLING_DATE']).dt.days
    hold_30_count = df[df['days_on_hold'] > 30]['ACCOUNT_NO'].nunique()

    # --- GROUPING ---
    month_total = df.groupby('month').size().reset_index(name='total_count')
    month_total = month_total.sort_values(
        by='month',
        key=lambda x: pd.to_datetime(x, format='%b %Y')
    )

    category_total = df.groupby('category').size().reset_index(name='total_count')

    df['category_grouped'] = df['category'].apply(
        lambda x: 'Space Out' if x == 'Space Out' else 'Business Suppression'
    )

    grouped_summary = df.groupby(['month', 'category_grouped']).size().reset_index(name='count')
    grouped_summary = grouped_summary.sort_values(
        by='month',
        key=lambda x: pd.to_datetime(x, format='%b %Y')
    )

    # --- TOP METRICS ---
    col1, col2 = st.columns(2)
    col1.markdown(f"""
    <div style="background-color:#4CAF50;padding:15px;border-radius:10px">
        <h4 style="color:white;">📌 Total Suppression</h4>
        <h2 style="color:white;">{grand_total}</h2>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div style="background-color:#FF5733;padding:15px;border-radius:10px">
        <h4 style="color:white;">⏳ >30 Days Hold</h4>
        <h2 style="color:white;">{hold_30_count}</h2>
    </div>
    """, unsafe_allow_html=True)
    # --- SINGLE ROW DASHBOARD (NO SCROLL) ---
    col3, col4, col5 = st.columns(3)

    TABLE_HEIGHT = 300

    with col3:
        st.subheader("📅 Month")
        st.dataframe(month_total.style.map(highlight_category, subset=['month']), height=TABLE_HEIGHT, use_container_width=True)

    with col4:
        st.subheader("📊 Category")
        st.dataframe(
            category_total.style.map(highlight_category, subset=['category']),
            use_container_width=True,
            height=TABLE_HEIGHT
        )
    with col5:
        st.subheader("📊 Split")
        st.dataframe(grouped_summary.style.map(highlight_category, subset=['category_grouped']), height=TABLE_HEIGHT, use_container_width=True)


