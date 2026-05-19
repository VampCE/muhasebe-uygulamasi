import streamlit as st
from datetime import date
from repo import fetch_dict, fetch_subcontractors, insert_record

def render(conn, cur):
    st.title("➕ Hızlı Kayıt")

    companies = fetch_dict(cur, "companies")
    employees = fetch_dict(cur, "employees")
    machines  = fetch_dict(cur, "machines")
    jobs      = fetch_dict(cur, "jobs")
    units     = fetch_dict(cur, "units")
    dumps     = fetch_dict(cur, "dump_sites")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        work_date = st.date_input("📅 Tarih", st.session_state.get("work_date", date.today()))
        st.session_state["work_date"] = work_date
    with col2:
        company = st.selectbox("🏢 Şirket", companies.keys(), index=0 if companies else None)
    with col3:
        machine = st.selectbox("🚜 Makine", machines.keys(), index=0 if machines else None)
    with col4:
        employee = st.selectbox("👷 Çalışan", employees.keys(), index=0 if employees else None)

    # --- Taşeron (opsiyonel, şirkete bağlı) ---
    subcontractor_id = None
    if company:
        subs = fetch_subcontractors(cur, companies[company])
        sub_choice = st.selectbox("🏗️ Taşeron (opsiyonel)", ["—"] + list(subs.keys()))
        subcontractor_id = None if sub_choice == "—" else subs[sub_choice]

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        job = st.selectbox("🧱 İş Türü", jobs.keys(), index=0 if jobs else None)
    with col6:
        quantity = st.number_input("🔢 Miktar", min_value=0.0, step=1.0)
    with col7:
        unit = st.selectbox("📏 Birim", units.keys(), index=0 if units else None)
    with col8:
        dump = st.selectbox("📍 Döküm (opsiyonel)", ["—"] + list(dumps.keys()))

    col9, col10 = st.columns(2)

    with col9:
        unit_price = st.number_input("💰 Birim Fiyat", min_value=0.0, step=1.0)

    # VINÇ için manuel tutar
    if machine and "vinç" in machine.lower():
        with col10:
            total = st.number_input("Tutar", min_value=0.0, step=1.0)
    else:
        total = quantity * unit_price
        with col10:
            st.metric("Tutar", f"{total:,.2f}")


    if st.button("💾 KAYDET", use_container_width=True):
        if not all([companies, employees, machines, jobs, units]):
            st.error("Önce Tanımlardan şirket/çalışan/makine/iş/birim ekle.")
            return
        if not all([company, employee, machine, job, unit]):
            st.error("Zorunlu alanlar eksik.")
            return

        insert_record(
            conn, cur,
            work_date,
            companies[company],
            employees[employee],
            machines[machine],
            jobs[job],
            quantity,
            units[unit],
            dumps.get(dump) if dump != "—" else None,
            unit_price,
            total,
            subcontractor_id=subcontractor_id
            )
        st.success("Kayıt eklendi.")
        st.rerun()
