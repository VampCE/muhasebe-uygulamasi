import os
import streamlit as st
from dotenv import load_dotenv
from db import get_conn

from pages.quick_entry import render as render_quick
from pages.master_data import render as render_master
from pages.list_export import render as render_list

load_dotenv()

st.set_page_config("Hafriyat Takip", layout="wide")

# DB
conn = get_conn()
cur = conn.cursor()

st.sidebar.title("Menü")
menu = st.sidebar.radio(
    "",
    ["➕ Hızlı Kayıt", "📚 Tanımlar", "📋 Liste / Export"]
)

if menu == "➕ Hızlı Kayıt":
    render_quick(conn, cur)

elif menu == "📚 Tanımlar":
    render_master(conn, cur)

elif menu == "📋 Liste / Export":
    render_list(conn, cur)
