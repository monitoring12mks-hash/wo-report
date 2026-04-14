import streamlit as st
import pandas as pd

# Setting halaman agar lebih ramping
st.set_page_config(page_title="WO Reporter", page_icon="📲")

# Sembunyikan menu bawaan streamlit agar lebih bersih saat di-screenshot
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("📲 Report Kerja Engineer")

uploaded_file = st.file_uploader("Upload file Excel/CSV di sini", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # Membaca file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Bersihkan nama kolom
        df.columns = [c.strip() for c in df.columns]

        # Pastikan kolom EngineerName, MerchantName, dan WorkActivity ada
        # Jika tidak ada, kita coba ambil berdasarkan posisi kolom
        eng_col = 'EngineerName' if 'EngineerName' in df.columns else df.columns[-1]
        merch_col = 'MerchantName' if 'MerchantName' in df.columns else df.columns[4]
        act_col = 'WorkActivity' if 'WorkActivity' in df.columns else df.columns[7]

        # Ubah semua ke string dan tangani data kosong
        df[eng_col] = df[eng_col].fillna("Tanpa Nama").astype(str)
        df[merch_col] = df[merch_col].fillna("-").astype(str)
        df[act_col] = df[act_col].fillna("-").astype(str)

        st.markdown("---")
        
        # Ambil daftar engineer unik dan urutkan
        engineers = sorted(df[eng_col].unique())

        # LOOP UTAMA: Membuat tampilan teks seperti gambar
        for engineer in engineers:
            group = df[df[eng_col] == engineer]
            
            # Tampilkan Nama Engineer (Bold)
            st.markdown(f"**{engineer}**")
            
            # Tampilkan list pekerjaan (Bullet points)
            for _, row in group.iterrows():
                # Format: Nama Merchant - Jenis Pekerjaan
                st.write(f"• {row[merch_col]} - {row[act_col]}")
            
            # Beri sedikit ruang antar engineer
            st.write("")

        st.markdown("---")
        st.caption("Gunakan screenshot HP untuk mengirim hasil di atas ke WhatsApp.")

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
