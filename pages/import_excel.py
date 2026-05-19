import streamlit as st
import pandas as pd
from repo import (
    fetch_dict,
    insert_name,
    insert_record
)


def render(conn, cur):
    st.title("📥 Excel'den Veri Yükle")

    companies = fetch_dict(cur, "companies")

    company_name = st.selectbox("Şirket", list(companies.keys()))

    uploaded_file = st.file_uploader("Excel dosyasını yükle", type=["xlsx"])

    if uploaded_file is None:
        return

    df = pd.read_excel(uploaded_file)

    st.subheader("Yüklenen Veri Önizleme")
    st.dataframe(df)

    required_cols = [
        "TARİH",
        "MAKİNE",
        "İŞ",
        "MİKTAR",
        "BİRİM",
        "BİRİM FYT"
    ]

    if not all(col in df.columns for col in required_cols):
        st.error("Excel kolonları eksik!")
        return

    if st.button("📤 Verileri İçeri Aktar"):

        # Default çalışan
        insert_name(conn, cur, "employees", "Excel Import")
        employees = fetch_dict(cur, "employees")
        default_employee_id = employees["Excel Import"]

        machines = fetch_dict(cur, "machines")
        jobs = fetch_dict(cur, "jobs")
        units = fetch_dict(cur, "units")

        rows_to_insert = []
        skipped_rows = []

        for idx, row in df.iterrows():

            try:
                if pd.isna(row["MİKTAR"]) or pd.isna(row["BİRİM FYT"]):
                    skipped_rows.append({
                        "Satır No": idx + 2,
                        "Sebep": "Miktar veya Birim Fiyat boş"
                    })
                    continue

                work_date = pd.to_datetime(row["TARİH"]).date()
                machine_name = str(row["MAKİNE"]).strip()
                job_name = str(row["İŞ"]).strip()
                unit_name = str(row["BİRİM"]).strip()

                quantity = float(row["MİKTAR"])
                unit_price = float(row["BİRİM FYT"])
                total = quantity * unit_price

                if machine_name not in machines:
                    insert_name(conn, cur, "machines", machine_name)
                    machines = fetch_dict(cur, "machines")

                if job_name not in jobs:
                    insert_name(conn, cur, "jobs", job_name)
                    jobs = fetch_dict(cur, "jobs")

                if unit_name not in units:
                    insert_name(conn, cur, "units", unit_name)
                    units = fetch_dict(cur, "units")

                rows_to_insert.append((
                    work_date,
                    companies[company_name],
                    default_employee_id,
                    machines[machine_name],
                    jobs[job_name],
                    quantity,
                    units[unit_name],
                    None,
                    unit_price,
                    total,
                    None
                ))

            except Exception as e:
                skipped_rows.append({
                    "Satır No": idx + 2,
                    "Sebep": str(e)
                })

        # ----------------------------
        # TEK SEFERDE INSERT
        # ----------------------------
        if rows_to_insert:
            cur.executemany("""
                INSERT INTO records
                (work_date, company_id, employee_id, machine_id, job_id,
                quantity, unit_id, dump_site_id, unit_price, total, subcontractor_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, rows_to_insert)

            conn.commit()

        st.success(f"{len(rows_to_insert)} kayıt eklendi.")

        if skipped_rows:
            st.warning(f"{len(skipped_rows)} satır atlandı.")
            st.dataframe(pd.DataFrame(skipped_rows))
