import streamlit as st
import pandas as pd
from database import get_user_history, get_supabase


def show_dashboard(username: str, is_admin: bool = False):
    """Show user dashboard with charts."""
    st.markdown("""
    <style>
    .stApp { background: #ffffff !important; }
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1.5px solid #ebebf5 !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] { 
        color: #ff3b3b !important; 
        font-size: 36px !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] { 
        color: #555580 !important;
        font-size: 12px !important;
    }
    .stDataFrame td { color: #1a1a2e !important; }
    .stDataFrame th { color: #555580 !important; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:24px; font-weight:700;
        color:#ff3b3b; margin-bottom:20px;'>
        Dashboard
    </div>
    """, unsafe_allow_html=True)

    history = get_user_history(username)

    if not history:
        st.info("No scan data yet. Run your first scan!")
        return

    df = pd.DataFrame(history)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style='background:#ffffff;
            border:1.5px solid #ebebf5;
            border-radius:12px;padding:20px;
            text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.06);'>
            <div style='font-size:36px;font-weight:800;
                color:#ff3b3b;'>{len(df)}</div>
            <div style='font-size:11px;color:#9999bb;
                text-transform:uppercase;letter-spacing:1px;
                margin-top:4px;font-weight:600;'>
                Total Scans</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background:#ffffff;
            border:1.5px solid #ebebf5;
            border-radius:12px;padding:20px;
            text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.06);'>
            <div style='font-size:36px;font-weight:800;
                color:#ff3b3b;'>
                {int(df["bugs_found"].sum())}</div>
            <div style='font-size:11px;color:#9999bb;
                text-transform:uppercase;letter-spacing:1px;
                margin-top:4px;font-weight:600;'>
                Total Bugs Found</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='background:#ffffff;
            border:1.5px solid #ebebf5;
            border-radius:12px;padding:20px;
            text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.06);'>
            <div style='font-size:36px;font-weight:800;
                color:#ff3b3b;'>
                {round(df["bugs_found"].mean(), 1)}</div>
            <div style='font-size:11px;color:#9999bb;
                text-transform:uppercase;letter-spacing:1px;
                margin-top:4px;font-weight:600;'>
                Avg Bugs Per Scan</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style='background:#ffffff;
            border:1.5px solid #ebebf5;
            border-radius:12px;padding:20px;
            text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.06);'>
            <div style='font-size:36px;font-weight:800;
                color:#ff3b3b;'>
                {int(df["weak_points_found"].sum())}</div>
            <div style='font-size:11px;color:#9999bb;
                text-transform:uppercase;letter-spacing:1px;
                margin-top:4px;font-weight:600;'>
                Weak Points Found</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    if len(df) > 1:
        st.markdown("**Bugs Found Over Time**")
        chart_data = df[["scanned_at",
                         "bugs_found"]].copy()
        chart_data["scanned_at"] = pd.to_datetime(
            chart_data["scanned_at"])
        chart_data = chart_data.set_index("scanned_at")
        st.line_chart(chart_data)

    st.markdown("**Weak Points vs Bugs Per Scan**")
    bar_data = df[["weak_points_found",
                   "bugs_found"]].tail(10)
    bar_data.columns = ["Weak Points", "Bugs Found"]
    st.bar_chart(bar_data)

    st.markdown("**Recent Scans**")
    display_df = df[["scanned_at", "weak_points_found",
                     "bugs_found"]].copy()
    display_df.columns = ["Date", "Weak Points",
                          "Bugs Found"]
    display_df["Date"] = display_df["Date"].str[:16]
    st.dataframe(display_df, use_container_width=True)
