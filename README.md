# Enterprise Fraud Risk & Intelligence Data System (EDS)

Prototipe **Enterprise Data System (EDS)** end-to-end untuk mengintegrasikan data transaksi e-commerce, log identitas perangkat, dan catatan investigasi audit guna mendeteksi serta memantau risiko *fraud*.

## 1. Arsitektur & Komponen Sistem
- **Data Sources (3 Sumber & Hybrid Data):**
  1. `data/train_transaction.csv` (*Structured* — 590.540 log transaksi utama)
  2. `data/train_identity.csv` (*Structured* — 144.233 data perangkat & jaringan)
  3. `data/fraud_audit_logs.json` (*Unstructured* — log teks catatan investigasi auditor)
- **Data Integration & Quality (`src/etl_pipeline.py`):** Pipeline ETL berbasis Python yang menerapkan 4 aspek *Data Quality* (*Uniqueness*, *Validity*, *Completeness*, dan *Consistency*).
- **Enterprise Data Repository (`output/enterprise_fraud_dw.db`):** Data Warehouse relasional berbasis SQLite dengan skema *Star Schema* (`fact_transactions`, `dim_card`, `dim_device`, dan `dim_audit_notes`).
- **Data Analytics & Dashboard (`src/dashboard.py` & `src/analytics_queries.sql`):** Dashboard interaktif berbasis Streamlit untuk monitoring KPI, pola jam rawan, kerugian per jaringan kartu, dan penelusuran log investigasi.

## 2. Sumber Dataset
Karena ukuran file dataset utama melebihi batas unggah GitHub (>100 MB), unduh dataset publik **IEEE-CIS Fraud Detection** secara gratis melalui Kaggle:
- **Link Dataset:** https://www.kaggle.com/competitions/ieee-fraud-detection/data
- Ekstrak file ZIP yang diunduh, lalu salin **`train_transaction.csv`** dan **`train_identity.csv`** ke dalam folder `data/`.

## 3. Panduan Instalasi & Replikasi
Pastikan Python (versi 3.9 atau lebih baru) sudah terpasang di sistem, lalu jalankan perintah berikut secara berurutan di terminal dari direktori utama proyek:

1. **Instalasi Dependensi:**
   ```bash
   pip install -r requirements.txt