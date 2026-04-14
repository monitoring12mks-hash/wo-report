import streamlit as st
import pandas as pd

# Konfigurasi halaman agar bersih
st.set_page_config(page_title="WO Reporter Pivot", layout="centered")

# CSS untuk tampilan teks ala WhatsApp
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    p { margin-bottom: 2px; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    .engineer-header { font-weight: bold; color: #000; margin-top: 15px; text-decoration: underline; }
    .date-header { font-weight: bold; color: #444; margin-left: 10px; margin-top: 5px; }
    .item-list { margin-left: 25px; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# Fungsi untuk reset aplikasi
def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.title("📲 Report Kerja Engineer")

# Upload File
uploaded_file = st.file_uploader("Upload file Excel / CSV", type=['xlsx', 'csv'], key="file_uploader")

if uploaded_file:
    try:
        # Membaca data
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Bersihkan nama kolom
        df.columns = [c.strip() for c in df.columns]

        # 1. FILTER WORK ACTIVITY (Manual Selection)
        if 'WorkActivity' in df.columns:
            all_activities = sorted(df['WorkActivity'].unique().astype(str))
            selected_activities = st.multiselect(
                "Pilih WorkActivity yang ingin ditampilkan:",
                options=all_activities,
                default=all_activities
            )
            # Terapkan filter
            df = df[df['WorkActivity'].isin(selected_activities)]
        else:
            st.warning("Kolom 'WorkActivity' tidak ditemukan.")

        # Tombol Mulai Lagi (Reset)
        if st.button("🔄 Mulai Dari Awal / Reset"):
            reset_app()

        st.markdown("---")

        # 2. PROSES DATA (Struktur Pivot)
        if not df.empty:
            # Format Tanggal
            date_col = 'ActualTargetDate'
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')

            # Urutkan berdasarkan hierarki Pivot
            df = df.sort_values(['EngineerName', 'ActualTargetDate', 'MerchantName'])

            # Grouping untuk Tampilan
            for eng, eng_group in df.groupby('EngineerName'):
                # Level 1: EngineerName
                st.markdown(f"<p class='engineer-header'>{str(eng).upper()}</p>", unsafe_allow_html=True)
                
                for dt, dt_group in eng_group.groupby('ActualTargetDate'):
                    # Level 2: ActualTargetDate
                    st.markdown(f"<p class='date-header'>📅 {dt}</p>", unsafe_allow_html=True)
                    
                    for _, row in dt_group.iterrows():
                        # Level 3: Merchant & Activity
                        merchant = row['MerchantName']
                        activity = row['WorkActivity']
                        st.markdown(f"<p class='item-list'>• {merchant} - {activity}</p>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.info("Selesai. Silakan screenshot hasil di atas.")
        else:
            st.warning("Tidak ada data untuk WorkActivity yang dipilih.")

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
        if st.button("Reset Aplikasi"):
            reset_app()
