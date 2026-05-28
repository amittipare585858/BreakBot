import streamlit as st
import pandas as pd
from database import get_user_history, get_supabase


def show_dashboard(username: str, is_admin: bool = False):
    """Show user dashboard with charts."""
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
        st.metric("Total Scans", len(df))
    with col2:
        st.metric("Total Bugs Found",
                  int(df["bugs_found"].sum()))
    with col3:
        st.metric("Avg Bugs Per Scan",
                  round(df["bugs_found"].mean(), 1))
    with col4:
        st.metric("Weak Points Found",
                  int(df["weak_points_found"].sum()))

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
