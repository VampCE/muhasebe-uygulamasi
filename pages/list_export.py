import streamlit as st
import pandas as pd
from datetime import date
from repo import fetch_dict, load_records_df, update_selected_rows
from exports import df_to_xlsx_bytes, pdf_template_bytes

def render(conn, cur):
    st.title("📋 Liste • Düzenle • Excel / PDF")

    companies = fetch_dict(cur, "companies")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        start = st.date_input("Başlangıç", value=date.today().replace(day=1))
    with col2:
        end = st.date_input("Bitiş", value=date.today())
    with col3:
        company_name = st.selectbox("Şirket", ["Tümü"] + list(companies.keys()))
    with col4:
        hide_dump = st.checkbox("Export'ta döküm yerini gizle", value=True)

    company_id = None if company_name == "Tümü" else companies[company_name]
    df = load_records_df(cur, start, end, company_id)

    if df.empty:
        st.info("Bu filtrelerde kayıt yok.")
        return

    st.caption("Satır seç → Miktar / Birim Fiyat / Tarih düzenle → Kaydet. (Tutar otomatik hesaplanır)")

    # EKRANDA ID GÖSTERMEYELİM
    display_df = df.drop(columns=["id"], errors="ignore")

    edited = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tarih": st.column_config.DateColumn("Tarih"),
            "Şirket": st.column_config.TextColumn("Şirket", disabled=True),
            "Makine": st.column_config.TextColumn("Makine", disabled=True),
            "Çalışan": st.column_config.TextColumn("Çalışan", disabled=True),
            "İş Türü": st.column_config.TextColumn("İş ", disabled=True),
            "Miktar": st.column_config.NumberColumn("Miktar", step=1.0),
            "Birim": st.column_config.TextColumn("Birim", disabled=True),
            "Birim Fiyat": st.column_config.NumberColumn("Birim Fiyat", step=1.0),
            "Tutar": st.column_config.NumberColumn("Tutar", disabled=True),
            "Döküm Yeri": st.column_config.TextColumn("Döküm Yeri", disabled=True),
            "Seç": st.column_config.CheckboxColumn("Seç"),
        }
    )

    # Kaydetme için id lazım -> edited_df'ye tekrar id ekleyelim (orijinal df'den align ederek)
    edited_with_id = edited.copy()
    edited_with_id.insert(0, "id", df["id"].values)

    selected = edited_with_id[edited_with_id["Seç"] == True].copy()
    st.write(f"Seçili satır: **{len(selected)}**")

    colA, colB, colC = st.columns(3)

    with colA:
        if st.button("💾 Seçili Satırları Kaydet", use_container_width=True):
            n = update_selected_rows(conn, cur, edited_with_id)
            if n == 0:
                st.warning("Kaydetmek için satır seç.")
            else:
                st.success(f"{n} satır güncellendi.")
                st.rerun()

    # Export: seçili varsa onu, yoksa filtreli tabloyu indir
    export_df = selected.drop(columns=["Seç"], errors="ignore") if not selected.empty else edited_with_id.drop(columns=["Seç"], errors="ignore")

    # Export'ta id asla olmasın
    export_df = export_df.drop(columns=["id"], errors="ignore")

    # Döküm yeri export'ta default gizli (senin kuralın)
    if hide_dump:
        export_df = export_df.drop(columns=["Döküm Yeri"], errors="ignore")

    # ---- Sütun seçme ----
    st.subheader("📤 Export Ayarları")

    all_cols = list(export_df.columns)

    # default: döküm yeri yok, diğerleri var
    default_cols = all_cols.copy()
    selected_cols = st.multiselect(
        "Excel/PDF'de görünecek sütunlar",
        options=all_cols,
        default=default_cols
    )

    if not selected_cols:
        st.warning("En az 1 sütun seçmelisin.")
        return

    export_df = export_df[selected_cols].copy()

    subtitle = f"Tarih: {start} - {end} | Şirket: {company_name}"

    with colB:
        st.download_button(
            "📥 Excel indir",
            data=df_to_xlsx_bytes(export_df),
            file_name="hakediş.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with colC:
        st.download_button(
            "📄 PDF indir",
            data=pdf_template_bytes(export_df, "Hakediş Listesi", subtitle),
            file_name="hakediş.pdf",
            mime="application/pdf",
            use_container_width=True
        )
