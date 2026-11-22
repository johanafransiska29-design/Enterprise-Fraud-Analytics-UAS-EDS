import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Enterprise Fraud Analytics", layout="wide")
st.title("Enterprise Fraud Risk & Intelligence Dashboard")
st.markdown("Sistem Monitoring Transaksi E-Commerce & Tata Kelola Risiko Terintegrasi")

# Koneksi ke Enterprise Data Warehouse
conn = sqlite3.connect('output/enterprise_fraud_dw.db')

# 1. KPI Cards
kpi = pd.read_sql_query("""
    SELECT 
        COUNT(*) AS total_tx,
        SUM(isFraud) AS total_fraud,
        ROUND(AVG(isFraud) * 100, 2) AS fraud_rate,
        ROUND(SUM(CASE WHEN isFraud = 1 THEN TransactionAmt ELSE 0 END), 2) AS total_loss
    FROM fact_transactions
""", conn).iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transaksi", f"{int(kpi['total_tx']):,}")
col2.metric("Kasus Fraud Terdeteksi", f"{int(kpi['total_fraud']):,}")
col3.metric("Fraud Rate", f"{kpi['fraud_rate']}%")
col4.metric("Total Kerugian Fraud", f"${kpi['total_loss']:,.2f}")

st.divider()

# 2. Grafik Tren Jam Rawan & Jaringan Kartu
c1, c2 = st.columns(2)

with c1:
    st.subheader("Pola Jam Rawan Transaksi Fraud (00:00 - 23:00)")
    df_hour = pd.read_sql_query("""
        SELECT transaction_hour AS Jam, SUM(isFraud) AS Jumlah_Fraud
        FROM fact_transactions GROUP BY transaction_hour ORDER BY Jam
    """, conn)
    st.line_chart(df_hour.set_index('Jam'))

with c2:
    st.subheader("Kerugian Fraud per Jaringan Kartu (USD)")
    df_card = pd.read_sql_query("""
        SELECT c.card4 AS Jaringan, ROUND(SUM(CASE WHEN f.isFraud = 1 THEN f.TransactionAmt ELSE 0 END), 2) AS Kerugian_USD
        FROM fact_transactions f JOIN dim_card c ON f.card_sk = c.card_sk
        GROUP BY c.card4 ORDER BY Kerugian_USD DESC
    """, conn)
    st.bar_chart(df_card.set_index('Jaringan'))

st.divider()

# 3. Tabel Integrasi Hybrid (Structured + Unstructured Audit Notes)
st.subheader("Log Investigasi Fraud Terintegrasi (Hybrid Data)")
status_filter = st.selectbox("Filter Status Tiket Investigasi:", ["Semua", "Escalated", "Closed-Confirmed"])

query_hybrid = """
    SELECT f.TransactionID, f.transaction_timestamp AS Waktu, f.TransactionAmt AS Nominal_USD,
           c.card4 AS Kartu, COALESCE(d.DeviceType, 'Unknown') AS Perangkat,
           a.ticket_status AS Status, a.investigator_note AS Catatan_Auditor
    FROM fact_transactions f
    JOIN dim_audit_notes a ON f.TransactionID = a.TransactionID
    LEFT JOIN dim_card c ON f.card_sk = c.card_sk
    LEFT JOIN dim_device d ON f.TransactionID = d.TransactionID
"""
if status_filter != "Semua":
    query_hybrid += f" WHERE a.ticket_status = '{status_filter}'"
query_hybrid += " ORDER BY f.TransactionAmt DESC LIMIT 20"

df_hybrid = pd.read_sql_query(query_hybrid, conn)
st.dataframe(df_hybrid, use_container_width=True)

conn.close()