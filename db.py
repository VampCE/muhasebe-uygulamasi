import os
import psycopg2
import streamlit as st

@st.cache_resource
def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))
