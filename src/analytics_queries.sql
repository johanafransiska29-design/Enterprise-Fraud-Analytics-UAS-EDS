-- ============================================================================
-- ENTERPRISE DATA SYSTEM (EDS) - ANALYTICAL QUERIES
-- Database: enterprise_fraud_dw.db (Star Schema)
-- ============================================================================

-- 1. EXECUTIVE KPI SUMMARY
-- Menghasilkan angka metrik utama untuk kartu KPI di bagian atas Dashboard
SELECT 
    COUNT(*) AS total_transaksi,
    SUM(isFraud) AS total_kasus_fraud,
    ROUND(AVG(isFraud) * 100, 2) AS fraud_rate_persen,
    ROUND(SUM(TransactionAmt), 2) AS total_nilai_transaksi_usd,
    ROUND(SUM(CASE WHEN isFraud = 1 THEN TransactionAmt ELSE 0 END), 2) AS total_kerugian_fraud_usd
FROM fact_transactions;


-- 2. ANALISIS FRAUD BERDASARKAN JARINGAN & TIPE KARTU (Star Schema JOIN)
-- Menggabungkan tabel fakta dengan dimensi kartu untuk melihat segmen kartu paling berisiko
SELECT 
    c.card4 AS jaringan_kartu,
    c.card6 AS tipe_kartu,
    COUNT(f.TransactionID) AS jumlah_transaksi,
    SUM(f.isFraud) AS jumlah_fraud,
    ROUND(AVG(f.isFraud) * 100, 2) AS persentase_fraud,
    ROUND(SUM(CASE WHEN f.isFraud = 1 THEN f.TransactionAmt ELSE 0 END), 2) AS kerugian_usd
FROM fact_transactions f
JOIN dim_card c ON f.card_sk = c.card_sk
GROUP BY c.card4, c.card6
HAVING COUNT(f.TransactionID) > 100
ORDER BY kerugian_usd DESC;


-- 3. ANALISIS FRAUD BERDASARKAN PERANGKAT (Multi-Source JOIN)
-- Menghubungkan transaksi utama dengan log identitas perangkat (Sumber Data ke-2)
SELECT 
    COALESCE(d.DeviceType, 'No Device Log') AS tipe_perangkat,
    COUNT(f.TransactionID) AS total_transaksi,
    SUM(f.isFraud) AS total_fraud,
    ROUND(AVG(f.isFraud) * 100, 2) AS fraud_rate_persen,
    ROUND(AVG(CASE WHEN f.isFraud = 1 THEN f.TransactionAmt END), 2) AS rata_rata_nominal_fraud
FROM fact_transactions f
LEFT JOIN dim_device d ON f.TransactionID = d.TransactionID
GROUP BY COALESCE(d.DeviceType, 'No Device Log')
ORDER BY total_fraud DESC;


-- 4. POLA JAM RAWAN FRAUD (Time-Series Analysis)
-- Menampilkan distribusi fraud berdasarkan jam (0-23) untuk grafik garis di Dashboard
SELECT 
    transaction_hour AS jam_transaksi,
    COUNT(*) AS total_transaksi,
    SUM(isFraud) AS jumlah_fraud,
    ROUND(AVG(isFraud) * 100, 2) AS fraud_rate_persen
FROM fact_transactions
GROUP BY transaction_hour
ORDER BY jam_transaksi ASC;


-- 5. TOP 10 DOMAIN EMAIL DENGAN KERUGIAN FRAUD TERTINGGI
-- Mengidentifikasi pola anomali berdasarkan penyedia layanan email pembeli
SELECT 
    P_emaildomain AS domain_email,
    COUNT(*) AS total_transaksi,
    SUM(isFraud) AS total_fraud,
    ROUND(AVG(isFraud) * 100, 2) AS fraud_rate_persen,
    ROUND(SUM(CASE WHEN isFraud = 1 THEN TransactionAmt ELSE 0 END), 2) AS total_kerugian_usd
FROM fact_transactions
WHERE P_emaildomain != 'Unknown'
GROUP BY P_emaildomain
HAVING COUNT(*) >= 50
ORDER BY total_kerugian_usd DESC
LIMIT 10;


-- 6. INTEGRASI DATA HYBRID (Structured + Unstructured Audit Logs)
-- Menggabungkan data transaksi terstruktur dengan catatan investigasi teks tidak terstruktur (Sumber ke-3)
SELECT 
    f.TransactionID,
    f.transaction_timestamp,
    f.TransactionAmt AS nominal_usd,
    c.card4 AS jaringan_kartu,
    COALESCE(d.DeviceType, 'Unknown') AS perangkat,
    a.log_id,
    a.ticket_status,
    a.investigator_note
FROM fact_transactions f
JOIN dim_audit_notes a ON f.TransactionID = a.TransactionID
LEFT JOIN dim_card c ON f.card_sk = c.card_sk
LEFT JOIN dim_device d ON f.TransactionID = d.TransactionID
ORDER BY f.TransactionAmt DESC
LIMIT 25;