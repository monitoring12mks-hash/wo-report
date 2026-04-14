import streamlit as st
import pandas as pd

st.set_page_config(page_title="WO Reporter", page_icon="📝")
st.title("📲 WhatsApp Report Generator")

uploaded_file = st.file_uploader("Upload File Excel / CSV (WO History)", type=['xlsx', 'csv'])

if uploaded_file:
    st.info("⏳ File sedang diproses, mohon tunggu...")
    try:
        # Membaca File
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.success("✅ File berhasil dibaca sistem!")
        
        # FITUR DEBUG: Tampilkan 3 baris pertama data mentah
        with st.expander("🔍 Klik di sini untuk melihat data asli Anda"):
            st.dataframe(df.head(3))
        
        # Mencari kolom secara otomatis (Abaikan huruf besar/kecil)
        kolom_status = [c for c in df.columns if 'status' in str(c).lower()]
        kolom_engineer = [c for c in df.columns if 'engineer' in str(c).lower()]
        
        if not kolom_status or not kolom_engineer:
            st.error("❌ Gagal: Kolom 'Status' atau 'EngineerName' tidak ditemukan!")
            st.warning("Apakah Anda yakin ini file mentah WO History? Bukan file Pivot atau hasil rekap?")
            st.stop()
            
        # Ambil nama kolom yang benar sesuai file Anda
        status_col = kolom_status[0]
        eng_col = kolom_engineer[0]

        # Cari yang statusnya Scheduled
        df_open = df[df[status_col].astype(str).str.contains('Scheduled|Open', case=False, na=False)].copy()
        
        st.subheader(f"📊 Ditemukan {len(df_open)} Pekerjaan Open")

        # Jika ada data, tampilkan laporan
        if len(df_open) > 0:
            st.markdown("---")
            for engineer, group in df_open.groupby(eng_col):
                st.markdown(f"### 👷 *{engineer}* ({len(group)} Task)")
                
                for i, row in group.iterrows():
                    # Coba cari kolom merchant dan activity secara dinamis
                    merchant = row.get('MerchantName', row.iloc[4] if len(row) > 4 else "Data Merchant")
                    activity = row.get('WorkActivity', row.iloc[7] if len(row) > 7 else "Data Aktivitas")
                    
                    st.markdown(f"• **{merchant}**\n  _{activity}_")
                st.markdown("---")
        else:
            st.warning("⚠️ Tidak ada pekerjaan dengan status 'Scheduled' di dalam file ini.")
            
    except Exception as e:
        st.error(f"❌ Terjadi Error Teknis: {e}")
        st.info("Pastikan Anda sudah menambahkan 'openpyxl' di dalam file requirements.txt Anda.")
