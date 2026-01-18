import pandas as pd

# ---------- Lookups ----------
def fetch_dict(cur, table: str) -> dict:
    cur.execute(f"SELECT id, name FROM {table} ORDER BY name")
    return {name: _id for _id, name in cur.fetchall()}

def insert_name(conn, cur, table: str, name: str):
    name = (name or "").strip()
    if not name:
        return
    cur.execute(
        f"INSERT INTO {table}(name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (name,)
    )
    conn.commit()

# ---------- Subcontractors (Taşeron) ----------
def fetch_subcontractors(cur, company_id: int) -> dict:
    cur.execute(
        "SELECT id, name FROM subcontractors WHERE company_id=%s ORDER BY name",
        (company_id,)
    )
    return {name: _id for _id, name in cur.fetchall()}

def insert_subcontractor(conn, cur, company_id: int, name: str):
    name = (name or "").strip()
    if not name:
        return
    cur.execute("""
        INSERT INTO subcontractors(company_id, name)
        VALUES (%s, %s)
        ON CONFLICT (company_id, name) DO NOTHING
    """, (company_id, name))
    conn.commit()

# ---------- Records ----------
def insert_record(
    conn, cur,
    work_date, company_id, employee_id, machine_id, job_id,
    quantity, unit_id, dump_site_id, unit_price,
    subcontractor_id=None
):
    qty = float(quantity or 0)
    up = float(unit_price or 0)
    total = qty * up

    cur.execute("""
        INSERT INTO records
        (work_date, company_id, employee_id, machine_id, job_id,
         quantity, unit_id, dump_site_id, unit_price, total, subcontractor_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        work_date, company_id, employee_id, machine_id, job_id,
        qty, unit_id, dump_site_id, up, total,
        subcontractor_id
    ))
    conn.commit()

def load_records_df(cur, start_date, end_date, company_id=None):
    q = """
    SELECT
      r.id,
      r.work_date AS "Tarih",
      c.name      AS "Şirket",
      COALESCE(sc.name,'') AS "Taşeron",
      m.name      AS "Makine",
      e.name      AS "Çalışan",
      j.name      AS "İş Türü",
      r.quantity  AS "Miktar",
      u.name      AS "Birim",
      r.unit_price AS "Birim Fiyat",
      r.total     AS "Tutar",
      COALESCE(d.name,'') AS "Döküm Yeri"
    FROM records r
    JOIN companies c ON c.id=r.company_id
    LEFT JOIN subcontractors sc ON sc.id=r.subcontractor_id
    JOIN machines  m ON m.id=r.machine_id
    JOIN employees e ON e.id=r.employee_id
    JOIN jobs      j ON j.id=r.job_id
    JOIN units     u ON u.id=r.unit_id
    LEFT JOIN dump_sites d ON d.id=r.dump_site_id
    WHERE r.work_date BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    if company_id:
        q += " AND r.company_id=%s"
        params.append(company_id)
    q += " ORDER BY r.work_date DESC, r.id DESC"

    cur.execute(q, params)
    rows = cur.fetchall()

    cols = ["id","Tarih","Şirket","Taşeron","Makine","Çalışan","İş Türü","Miktar","Birim","Birim Fiyat","Tutar","Döküm Yeri"]
    df = pd.DataFrame(rows, columns=cols)
    df.insert(0, "Seç", False)
    return df

def update_selected_rows(conn, cur, edited_df):
    selected = edited_df[edited_df["Seç"] == True].copy()
    if selected.empty:
        return 0

    for _, r in selected.iterrows():
        rid = int(r["id"])
        qty = float(r["Miktar"] or 0)
        up  = float(r["Birim Fiyat"] or 0)
        total = qty * up

        cur.execute("""
            UPDATE records
            SET work_date=%s,
                quantity=%s,
                unit_price=%s,
                total=%s
            WHERE id=%s
        """, (r["Tarih"], qty, up, total, rid))

    conn.commit()
    return len(selected)
