import streamlit as st
import pandas as pd
from repo import (
    fetch_dict,
    insert_name,
    fetch_subcontractors,
    insert_subcontractor
)

def render(conn, cur):
    st.title("📚 Tanımlar")

    tabs = st.tabs([
        "🏢 Şirket",
        "👷 Çalışan",
        "🚜 Makine",
        "📏 Birim",
        "🧱 İş Türü",
        "📍 Döküm",
        "🏗️ Taşeron"
    ])

    # Standart tablolar
    mapping = [
        ("companies", "Şirket", tabs[0]),
        ("employees", "Çalışan", tabs[1]),
        ("machines",  "Makine", tabs[2]),
        ("units",     "Birim", tabs[3]),
        ("jobs",      "İş Türü", tabs[4]),
        ("dump_sites","Döküm Yeri", tabs[5]),
    ]

    for table, label, tab in mapping:
        with tab:
            name = st.text_input(f"Yeni {label}", key=f"{table}_name")
            if st.button("➕ Ekle", key=f"{table}_add"):
                insert_name(conn, cur, table, name)
                st.success("Eklendi.")
                st.rerun()

            st.divider()
            d = fetch_dict(cur, table)
            st.dataframe(pd.DataFrame(d.keys(), columns=[label]), use_container_width=True)

    # Taşeron sekmesi (şirkete bağlı)
    with tabs[6]:
        companies = fetch_dict(cur, "companies")

        if not companies:
            st.info("Önce Şirket tanımı yapmalısın.")
            return

        company_name = st.selectbox("Şirket Seç", list(companies.keys()), key="sub_company")
        company_id = companies[company_name]

        sub_name = st.text_input("Yeni Taşeron Adı", key="sub_name")

        colA, colB = st.columns([1, 2])
        with colA:
            if st.button("➕ Taşeron Ekle", use_container_width=True):
                insert_subcontractor(conn, cur, company_id, sub_name)
                st.success("Taşeron eklendi.")
                st.rerun()

        st.divider()
        subs = fetch_subcontractors(cur, company_id)
        st.write(f"**{company_name}** taşeronları:")
        st.dataframe(pd.DataFrame(subs.keys(), columns=["Taşeron"]), use_container_width=True)