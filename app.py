import streamlit as st
import pandas as pd

# 1. SETTING CSS & TAMPILAN
st.set_page_config(page_title="WO Reporter Pro", layout="centered")

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
    </style>
    """, unsafe_allow_html=True)

# 2. FUNGSI AMBIL DATA PEMBANDING DARI GOOGLE SHEETS
@st.cache_data(ttl=600) # Data disimpan selama 10 menit sebelum refresh otomatis
def get_blacklist_data(sheet_url):
    # Mengubah URL biasa ke URL format ekspor CSV
    csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
    try:
        blacklist_df = pd.read_csv(csv_url)
        return blacklist_df['TicketNo'].astype(str).unique().tolist()
    except:
        return []

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.title("📲 Pro WO Reporter")

# GANTI INI dengan Link Google Sheets Anda
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mhdwIlP20HmtmlYb0BP-vfH32jiE82m5GGq6_yCaYSk/edit?gid=758149661#gid=758149661"

blacklist_tickets = get_blacklist_data(GOOGLE_SHEET_URL)

uploaded_files = st.file_uploader("Upload file WO History", type=['xlsx', 'csv'], accept_multiple_files=True)

if uploaded_files:
    try:
        all_df = []
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith('.csv'):
                temp_df = pd.read_csv(uploaded_file)
            else:
                temp_df = pd.read_excel(uploaded_file, engine='openpyxl')
            temp_df.columns = [c.strip() for c in temp_df.columns]
            all_df.append(temp_df)
        
        df = pd.concat(all_df, ignore_index=True)

        # FITUR: FILTER DATA PEMBANDING (Berdasarkan Google Sheets)
        if 'TicketNo' in df.columns and len(blacklist_tickets) > 0:
            initial_count = len(df)
            # Menghapus data yang TicketNo-nya ada di daftar blacklist
            df = df[~df['TicketNo'].astype(str).isin(blacklist_tickets)]
            removed_count = initial_count - len(df)
            if removed_count > 0:
                st.warning(f"ℹ️ {removed_count} data disembunyikan (Cocok dengan data pembanding)")

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
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')

            df = df.sort_values(['EngineerName', 'ActualTargetDate', 'MerchantName'])

            full_text_report = ""
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
            st.text_area("Copy Teks Laporan:", value=full_text_report, height=250)
            
    except Exception as e:
        st.error(f"Error: {e}")
