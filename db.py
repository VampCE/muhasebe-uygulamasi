import os
import psycopg2
import streamlit as st

def get_conn():
    db_url = None

    if "DATABASE_URL" in st.secrets
    db_url = st.secrets.get("DATABASE_URL")
    try:
        return psycopg2.connect(db_url)
    except Exception as e:
        st.error(f"DB hata: {type(e).__name__} - {e}")
        raise
    else:
        db_url = os.getenv("DATABASE_URL")

    if not db_url:
        raise RuntimeError("DATABASE_URL tanımlı değil")

    return psycopg2.connect(db_url)
