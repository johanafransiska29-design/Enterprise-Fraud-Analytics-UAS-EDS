import pandas as pd
import json
import sqlite3
import os
from datetime import datetime, timedelta

# Pastikan folder output tersedia
os.makedirs('output', exist_ok=True)

print("1. EXTRACT: Membaca dataset dari folder data/...")
tx_cols = [
    'TransactionID', 'isFraud', 'TransactionDT', 'TransactionAmt',
    'ProductCD', 'card1', 'card2', 'card4', 'card6', 'addr1', 'P_emaildomain'
]
id_cols = ['TransactionID', 'DeviceType', 'DeviceInfo', 'id_30', 'id_31']

df_tx = pd.read_csv('data/train_transaction.csv', usecols=tx_cols)
df_id = pd.read_csv('data/train_identity.csv', usecols=id_cols)

# Buat Sumber Data ke-3 (Unstructured JSON) di folder data/
print("   Membuat Sumber Data ke-3 (data/fraud_audit_logs.json)...")
sample_fraud = df_tx[df_tx['isFraud'] == 1].head(500)
audit_logs = []
notes_templates = [
    "URGENT: Nasabah melaporkan transaksi tidak dikenal dari perangkat baru pada dini hari.",
    "ALERT: Percobaan transaksi berulang dalam waktu singkat melewati batas wajar.",
    "REVIEW: Alamat IP dan domain email pembeli tidak sesuai dengan profil kartu terdaftar.",
    "INVESTIGATION: Transaksi nominal tinggi terdeteksi pada merchant kategori berisiko."
]

for idx, row in sample_fraud.iterrows():
    audit_logs.append({
        "log_id": f"AUD-{int(row['TransactionID'])}",
        "TransactionID": int(row['TransactionID']),
        "investigator_note": notes_templates[idx % len(notes_templates)],
        "ticket_status": "Escalated" if row['TransactionAmt'] > 200 else "Closed-Confirmed"
    })

with open('data/fraud_audit_logs.json', 'w') as f:
    json.dump(audit_logs, f, indent=2)

df_logs = pd.read_json('data/fraud_audit_logs.json')

print("\n2. TRANSFORM & DATA QUALITY CHECK:")
initial_rows = len(df_tx)

# DQ 1: Uniqueness
df_tx = df_tx.drop_duplicates(subset=['TransactionID'])
df_id = df_id.drop_duplicates(subset=['TransactionID'])
dup_removed = initial_rows - len(df_tx)

# DQ 2: Validity
invalid_amt = len(df_tx[df_tx['TransactionAmt'] <= 0])
df_tx = df_tx[df_tx['TransactionAmt'] > 0]

# DQ 3: Completeness
null_cards_before = df_tx['card4'].isnull().sum()
df_tx['card4'] = df_tx['card4'].fillna('Unknown')
df_tx['card6'] = df_tx['card6'].fillna('Unknown')
df_tx['P_emaildomain'] = df_tx['P_emaildomain'].fillna('Unknown')
df_id['DeviceType'] = df_id['DeviceType'].fillna('Unknown')
df_id['DeviceInfo'] = df_id['DeviceInfo'].fillna('Unknown')

# DQ 4: Consistency
df_tx['card4'] = df_tx['card4'].str.upper().str.strip()
df_tx['card6'] = df_tx['card6'].str.upper().str.strip()
df_id['DeviceType'] = df_id['DeviceType'].str.capitalize().str.strip()

# Konversi waktu
base_date = datetime(2025, 12, 1)
df_tx['transaction_timestamp'] = df_tx['TransactionDT'].apply(
    lambda x: (base_date + timedelta(seconds=int(x))).strftime('%Y-%m-%d %H:%M:%S')
)
df_tx['transaction_hour'] = pd.to_datetime(df_tx['transaction_timestamp']).dt.hour

# Simpan laporan Data Quality ke folder output/
dq_report = pd.DataFrame([
    {"Aspek_DQ": "Uniqueness", "Metric": "Duplikat TransactionID dihapus", "Nilai": dup_removed},
    {"Aspek_DQ": "Validity", "Metric": "Transaksi nominal <= 0 dihapus", "Nilai": invalid_amt},
    {"Aspek_DQ": "Completeness", "Metric": "Null card4 diimputasi 'Unknown'", "Nilai": null_cards_before},
    {"Aspek_DQ": "Consistency", "Metric": "Standardisasi Uppercase/Capitalize", "Nilai": len(df_tx)}
])
dq_report.to_csv('output/data_quality_report.csv', index=False)
print(dq_report)

print("\n3. LOAD: Menyimpan Data Warehouse ke output/enterprise_fraud_dw.db...")
conn = sqlite3.connect('output/enterprise_fraud_dw.db')

# Dimensi 1: dim_card
dim_card = df_tx[['card1', 'card4', 'card6']].drop_duplicates().reset_index(drop=True)
dim_card['card_sk'] = dim_card.index + 1
dim_card.to_sql('dim_card', conn, if_exists='replace', index=False)

# Dimensi 2: dim_device
dim_device = df_id[['TransactionID', 'DeviceType', 'DeviceInfo', 'id_30', 'id_31']].copy()
dim_device.to_sql('dim_device', conn, if_exists='replace', index=False)

# Dimensi 3: dim_audit_notes
df_logs.to_sql('dim_audit_notes', conn, if_exists='replace', index=False)

# Fakta: fact_transactions
fact_tx = df_tx.merge(dim_card, on=['card1', 'card4', 'card6'], how='left')
fact_cols = [
    'TransactionID', 'card_sk', 'transaction_timestamp', 'transaction_hour',
    'TransactionAmt', 'ProductCD', 'P_emaildomain', 'isFraud'
]
fact_tx[fact_cols].to_sql('fact_transactions', conn, if_exists='replace', index=False)

# Indexing
conn.execute("CREATE INDEX idx_fact_tx_id ON fact_transactions(TransactionID);")
conn.execute("CREATE INDEX idx_fact_fraud ON fact_transactions(isFraud);")
conn.execute("CREATE INDEX idx_dim_dev_tx ON dim_device(TransactionID);")

conn.close()
print("\nSELESAI! Cek folder output/ untuk melihat database dan laporan DQ.")