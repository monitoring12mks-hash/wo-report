import streamlit as st
import pandas as pd

# Konfigurasi Tampilan
st.set_page_config(page_title="WO Open Report", layout="wide")

st.title("📊 WO Open Schedule Reporter")
st.write("Upload file Excel untuk menghasilkan laporan WhatsApp")

uploaded_file = st.file_uploader("Pilih file Excel (WO History)", type=['xlsx', 'csv'])

if uploaded_file:
    # Membaca Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # 1. Filter Status 'Scheduled' (Open)
    # Sesuaikan 'Status' dengan nama kolom di excel Anda jika berbeda
    df_open = df[df['Status'] == 'Scheduled'].copy()
    
    # 2. Ambil Kolom Penting saja untuk diringkas
    columns_to_show = ['EngineerName', 'MerchantName', 'WorkActivity', 'ActualTargetDate']
    df_filtered = df_open[columns_to_show]

    # 3. Styling Laporan (Agar cantik saat di-screenshot)
    st.subheader("📋 Ringkasan Laporan")
    
    # Mengelompokkan berdasarkan Engineer untuk mempermudah pembacaan
    for engineer, group in df_filtered.groupby('EngineerName'):
        with st.expander(f"👷 {engineer} ({len(group)} Task)", expanded=True):
            # Menghilangkan index agar lebih bersih
            st.table(group[['MerchantName', 'WorkActivity']])
            
    st.success("Tips: Gunakan Dark Mode atau Light Mode sesuai selera, lalu screenshot bagian ini untuk dikirim ke WA.")
