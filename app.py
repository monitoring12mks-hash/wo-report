import streamlit as st
import pandas as pd

# Konfigurasi halaman
st.set_page_config(page_title="WO Reporter Full", page_icon="📝")

st.title("📲 WhatsApp Report Generator (All Data)")
st.write("Laporan otomatis berdasarkan semua data di file Excel/CSV")

uploaded_file = st.file_uploader("Upload File WO History", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # Membaca File
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Bersihkan nama kolom dari spasi yang tidak sengaja ada
        df.columns = [c.strip() for c in df.columns]
        
        # Cek apakah kolom yang dibutuhkan ada
        required_cols = ['EngineerName', 'MerchantName', 'WorkActivity']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Kolom berikut tidak ditemukan: {', '.join(missing_cols)}")
            st.info("Pastikan Anda menggunakan file WO History yang asli.")
        else:
            # Tampilan Ringkasan
            st.subheader(f"✅ Total {len(df)} Data Ditampilkan")
            st.markdown("---")
            
            # Kelompokkan berdasarkan Engineer (Semua Data Tampil)
            # Kita urutkan nama Engineer agar rapi
            engineers = sorted(df['EngineerName'].unique().astype(str))
            
            for engineer in engineers:
                group = df[df['EngineerName'] == engineer]
                
                # Header Nama Engineer
                st.markdown(f"### 👷 *{engineer}* ({len(group)} Task)")
                
                # List pekerjaan di bawah nama engineer
                for i, row in group.iterrows():
                    # Menampilkan Merchant dan Aktivitas
                    st.markdown(f"• **{row['MerchantName']}**\n  _{row['WorkActivity']}_")
                
                st.markdown("---") # Garis pembatas antar engineer
            
            st.success("Selesai! Silakan screenshot hasil di atas untuk dikirim ke WhatsApp.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
