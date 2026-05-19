import psycopg2
import streamlit as st
import os
from dotenv import load_dotenv


load_dotenv()

def get_conn():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL bulunamadı")
    return psycopg2.connect(db_url)