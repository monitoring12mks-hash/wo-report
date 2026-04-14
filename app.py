import streamlit as st
import pandas as pd

# Konfigurasi halaman
st.set_page_config(page_title="WO Reporter Full", page_icon="📝")

st.title("📲 WhatsApp Report Generator")
st.write("Menampilkan semua data dari file WO History")

uploaded_file = st.file_uploader("Upload File Excel / CSV", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # Membaca File
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Bersihkan nama kolom dari spasi
        df.columns = [c.strip() for c in df.columns]
        
        # Pastikan kolom EngineerName, MerchantName, dan WorkActivity ada
        # Jika nama kolom berbeda di file Anda, kode ini akan mencoba mencarinya
        eng_col = 'EngineerName' if 'EngineerName' in df.columns else df.columns[-1]
        merch_col = 'MerchantName' if 'MerchantName' in df.columns else df.columns[4]
        act_col = 'WorkActivity' if 'WorkActivity' in df.columns else df.columns[7]

        # MENGATASI ERROR: Ubah semua nama engineer menjadi teks dan isi yang kosong dengan "Tanpa Nama"
        df[eng_col] = df[eng_col].fillna("Belum Ditentukan").astype(str)
        
        # Tampilan Ringkasan
        st.subheader(f"✅ Total {len(df)} Data Berhasil Dimuat")
        st.markdown("---")
        
        # Urutkan berdasarkan Engineer (Sekarang aman dari error '<')
        engineers = sorted(df[eng_col].unique())
        
        for engineer in engineers:
            group = df[df[eng_col] == engineer]
            
            # Header Nama Engineer
            st.markdown(f"### 👷 *{engineer}* ({len(group)} Task)")
            
            # Daftar pekerjaan di bawah nama engineer
            for i, row in group.iterrows():
                m_name = str(row[merch_col]) if pd.notna(row[merch_col]) else "Merchant Tidak Diketahui"
                w_act = str(row[act_col]) if pd.notna(row[act_col]) else "Aktivitas Tidak Diketahui"
                
                st.markdown(f"• **{m_name}**\n  _{w_act}_")
            
            st.markdown("---")
            
        st.success("Selesai! Silakan screenshot hasil di atas.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
        st.info("Saran: Pastikan file yang diupload adalah file data mentah (WO History).")
