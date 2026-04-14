import streamlit as st
import pandas as pd

# 1. SETTING CSS & TAMPILAN (Anti-Dark Mode)
st.set_page_config(page_title="WO Reporter Multi-File", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    p, span, label, div { color: black !important; }
    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }
    .stButton>button { background-color: #f0f0f0; color: black; border: 1px solid #ccc; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.title("📲 Multi-File WO Reporter")

# FITUR: Upload lebih dari satu file (Multi-file)
uploaded_files = st.file_uploader("Upload satu atau beberapa file Excel / CSV", type=['xlsx', 'csv'], accept_multiple_files=True, key="uploader")

if uploaded_files:
    try:
        all_df = []
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith('.csv'):
                temp_df = pd.read_csv(uploaded_file)
            else:
                temp_df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Bersihkan nama kolom tiap file
            temp_df.columns = [c.strip() for c in temp_df.columns]
            all_df.append(temp_df)
        
        # MENGGABUNGKAN SEMUA FILE MENJADI SATU
        df = pd.concat(all_df, ignore_index=True)
        
        # Hapus duplikat jika ada (berdasarkan TicketNo jika ada kolomnya)
        if 'TicketNo' in df.columns:
            df = df.drop_duplicates(subset=['TicketNo'])

        # Filter WorkActivity
        if 'WorkActivity' in df.columns:
            all_activities = sorted(df['WorkActivity'].unique().astype(str))
            selected_activities = st.multiselect("Filter WorkActivity:", options=all_activities, default=all_activities)
            df = df[df['WorkActivity'].isin(selected_activities)]

        if st.button("🔄 Mulai Dari Awal"):
            reset_app()

        st.markdown("---")

        if not df.empty:
            date_col = 'ActualTargetDate'
            if date_col in df.columns:
                # Mengubah ke format tanggal tanpa jam agar pengelompokan rapi
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')

            # Urutkan berdasarkan hierarki Pivot
            df = df.sort_values(['EngineerName', 'ActualTargetDate', 'MerchantName'])

            full_text_report = ""

            # Loop untuk Tampilan Laporan
            for eng, eng_group in df.groupby('EngineerName'):
                header = f"{str(eng).upper()}"
                st.markdown(f"<p class='engineer-header'>{header}</p>", unsafe_allow_html=True)
                full_text_report += f"*{header}*\n"
                
                for dt, dt_group in eng_group.groupby('ActualTargetDate'):
                    date_line = f"📅 {dt}"
                    st.markdown(f"<p class='date-header'>{date_line}</p>", unsafe_allow_html=True)
                    full_text_report += f"{date_line}\n"
                    
                    for _, row in dt_group.iterrows():
                        item = f"• {row['MerchantName']} - {row['WorkActivity']}"
                        st.markdown(f"<p class='item-list'>{item}</p>", unsafe_allow_html=True)
                        full_text_report += f"{item}\n"
                full_text_report += "\n"

            st.markdown("---")
            
            # Bagian Copy Teks
            st.subheader("📋 Copy Hasil Gabungan")
            st.text_area("Klik/Tahan lalu 'Select All' & 'Copy' untuk Paste ke WhatsApp:", value=full_text_report, height=250)
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat menggabung file: {e}")
