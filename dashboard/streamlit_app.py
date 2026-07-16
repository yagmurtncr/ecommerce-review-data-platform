"""Streamlit dashboard for the E-Commerce Review Intelligence Platform.

Reads headline metrics from the analytics API (which sits on top of the
PostgreSQL star schema). Falls back to a local CSV so the dashboard renders
even before the warehouse is populated.

Run:  streamlit run dashboard/streamlit_app.py
"""
from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st

API = os.getenv("ANALYTICS_API", "http://localhost:8000")

st.set_page_config(page_title="Review Intelligence", page_icon="📊", layout="wide")
st.title("📊 E-Commerce Review Intelligence")


def api_get(path: str):
    try:
        r = requests.get(f"{API}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


overview = api_get("/analytics/overview")
by_cat = api_get("/analytics/by-category")
daily = api_get("/analytics/daily")

if overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total reviews", overview.get("total_reviews", 0))
    c2.metric("Avg rating", overview.get("avg_rating", 0))
    c3.metric("Avg sentiment", overview.get("avg_sentiment", 0))
    c4.metric("Suspicious", overview.get("suspicious_reviews", 0))
else:
    st.info("Analytics API not reachable yet — start the stack and run the batch pipeline "
            "(`make batch`). Showing an empty dashboard for now.")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Reviews & rating by category")
    if by_cat:
        df = pd.DataFrame(by_cat)
        st.bar_chart(df.set_index("category_name")["reviews"])
        st.dataframe(df, use_container_width=True)

with col_b:
    st.subheader("Daily review volume")
    if daily:
        df = pd.DataFrame(daily)
        df["full_date"] = pd.to_datetime(df["full_date"])
        st.line_chart(df.set_index("full_date")["reviews"])

st.subheader("🔎 Live sentiment check")
txt = st.text_input("Type a review to score:", "Fast shipping and great quality, love it!")
if st.button("Score") and txt:
    res = api_get("/predict") or {}
    # /predict is POST; call it directly
    try:
        res = requests.post(f"{API}/predict", json={"text": txt}, timeout=5).json()
        st.json(res)
    except Exception:
        st.warning("API not reachable.")
