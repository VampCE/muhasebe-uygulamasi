import streamlit as st
import pandas as pd
from datetime import date
from repo import (
    fetch_dict,
    fetch_subcontractors,
    load_records_df,
    update_selected_rows,
    delete_selected_rows
)
from exports import df_to_xlsx_bytes, pdf_template_bytes


def render(conn, cur):
    st.title("📋 Liste • Düzenle • Excel / PDF")

    # LOOKUPS
    companies = fetch_dict(cur, "companies")
    machines = fetch_dict(cur, "machines")
    employees = fetch_dict(cur, "employees")

    # FİLTRELER
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        start = st.date_input("Başlangıç", value=date.today().replace(day=1))

    with col2:
        end = st.date_input("Bitiş", value=date.today())

    with col3:
        company_name = st.selectbox(
            "Şirket",
            ["Tümü"] + list(companies.keys())
        )

    with col4:
        hide_dump = st.checkbox("Export'ta döküm yerini gizle", value=True)

    col5, col6, col7 = st.columns(3)

    with col5:
        machine_name = st.selectbox(
            "Makine",
            ["Tümü"] + list(machines.keys())
        )

    with col6:
        employee_name = st.selectbox(
            "Çalışan",
            ["Tümü"] + list(employees.keys())
        )

    subcontractor_name = "Tümü"
    if company_name != "Tümü":
        subs = fetch_subcontractors(cur, companies[company_name])
        with col7:
            subcontractor_name = st.selectbox(
                "Taşeron",
                ["Tümü"] + list(subs.keys())
            )

    company_id = None if company_name == "Tümü" else companies[company_name]

    df = load_records_df(cur, start, end, company_id)

    if machine_name != "Tümü":
        df = df[df["Makine"] == machine_name]

    if employee_name != "Tümü":
        df = df[df["Çalışan"] == employee_name]

    if subcontractor_name != "Tümü":
        df = df[df["Taşeron"] == subcontractor_name]

    if df.empty:
        st.info("Bu filtrelerde kayıt yok.")
        return

    st.caption("Satır seç → Düzenle → Kaydet veya Sil.")

    display_df = df.drop(columns=["id"], errors="ignore")

    edited = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tarih": st.column_config.DateColumn("Tarih"),
            "Şirket": st.column_config.TextColumn("Şirket"),
            "Makine": st.column_config.TextColumn("Makine"),
            "Çalışan": st.column_config.TextColumn("Çalışan"),
            "Taşeron": st.column_config.TextColumn("Taşeron"),
            "İş Türü": st.column_config.TextColumn("İş Türü"),
            "Miktar": st.column_config.NumberColumn("Miktar", step=1.0),
            "Birim": st.column_config.TextColumn("Birim"),
            "Birim Fiyat": st.column_config.NumberColumn("Birim Fiyat", step=1.0),
            "Tutar": st.column_config.NumberColumn("Tutar"),
            "Döküm Yeri": st.column_config.TextColumn("Döküm Yeri"),
            "Seç": st.column_config.CheckboxColumn("Seç"),
        }
    )

    edited_with_id = edited.copy()
    edited_with_id.insert(0, "id", df["id"].values)

    selected = edited_with_id[edited_with_id["Seç"] == True].copy()
    st.write(f"Seçili satır: **{len(selected)}**")

    colA, colB = st.columns(2)

    with colA:
        if st.button("💾 Seçili Satırları Kaydet", use_container_width=True):
            n = update_selected_rows(conn, cur, edited_with_id)
            if n == 0:
                st.warning("Kaydetmek için satır seç.")
            else:
                st.success(f"{n} satır güncellendi.")
                st.rerun()

    with colB:
        if st.button("🗑️ Seçili Satırları Sil", use_container_width=True):
            n = delete_selected_rows(conn, cur, edited_with_id)
            if n == 0:
                st.warning("Silmek için satır seç.")
            else:
                st.success(f"{n} satır silindi.")
                st.rerun()

    export_df = (
        selected.drop(columns=["Seç"], errors="ignore")
        if not selected.empty
        else edited_with_id.drop(columns=["Seç"], errors="ignore")
    )

    export_df = export_df.drop(columns=["id"], errors="ignore")

    if hide_dump:
        export_df = export_df.drop(columns=["Döküm Yeri"], errors="ignore")

    st.divider()
    st.subheader("📤 Export Ayarları")

    # AVANS
    avans = st.number_input(
        "Avans (toplamdan düşülecek)",
        min_value=0.0,
        value=0.0,
        step=100.0
    )

    group_machine = st.checkbox("PDF'te makineleri ayrı tablo yap", value=False)

    include_kdv = st.checkbox("PDF'te KDV hesapla", value=False)
    kdv_rate = 20

    if include_kdv:
        kdv_rate = st.number_input("KDV %", value=20)

    all_cols = list(export_df.columns)

    selected_cols = st.multiselect(
        "Excel/PDF'de görünecek sütunlar",
        options=all_cols,
        default=all_cols
    )

    if not selected_cols:
        st.warning("En az 1 sütun seçmelisin.")
        return

    export_df = export_df[selected_cols].copy()

    subtitle = f"Tarih: {start} - {end} | Şirket: {company_name}"

    colX, colY = st.columns(2)

    with colX:
        st.download_button(
            "📥 Excel indir",
            data=df_to_xlsx_bytes(export_df),
            file_name=f"{company_name}_hakediş.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with colY:
        st.download_button(
            "📄 PDF indir",
            data=pdf_template_bytes(
                export_df,
                "Muratoğlu Hakediş Listesi",
                subtitle,
                group_by_machine=group_machine,
                include_kdv=include_kdv,
                kdv_rate=kdv_rate,
                avans=avans
            ),
            file_name=f"{company_name}_hakediş.pdf",
            mime="application/pdf",
            use_container_width=True
        )