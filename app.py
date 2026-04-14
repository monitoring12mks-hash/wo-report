import streamlit as st
import pandas as pd

# Tema Putih Bersih
st.set_page_config(page_title="WhatsApp Reporter", layout="centered")

# CSS untuk menghilangkan semua dekorasi Streamlit agar teks terlihat bersih
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .reportview-container .main .block-container {padding-top: 1rem;}
    p { margin-bottom: 0px; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # Membaca data
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Standarisasi kolom
        df.columns = [c.strip() for c in df.columns]
        
        # Nama kolom sesuai file Anda
        eng_col = 'EngineerName'
        merch_col = 'MerchantName'
        act_col = 'WorkActivity'

        # Pastikan kolom ada, jika tidak, pakai posisi (fallback)
        if eng_col not in df.columns: eng_col = df.columns[-1]
        if merch_col not in df.columns: merch_col = df.columns[4]
        if act_col not in df.columns: act_col = df.columns[7]

        # Menampilkan data tanpa elemen UI yang mengganggu
        engineers = df[eng_col].unique()

        for engineer in engineers:
            if pd.isna(engineer): continue
            
            # Cetak Nama Engineer (Tebal)
            st.markdown(f"**{str(engineer).upper()}**")
            
            group = df[df[eng_col] == engineer]
            for _, row in group.iterrows():
                # Format: Nama Merchant - Aktivitas
                merchant = str(row[merch_col])
                activity = str(row[act_col])
                st.write(f"• {merchant} - {activity}")
            
            # Spasi antar engineer
            st.write("")

    except Exception as e:
        st.error("Pastikan file yang diupload benar.")
