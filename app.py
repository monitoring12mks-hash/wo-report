import streamlit as st
import pandas as pd

# 1. SETTING CSS & TAMPILAN (Anti-Dark Mode)
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
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Inisialisasi session state untuk reset
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def reset_app():
    # Menaikkan nilai key agar uploader ter-reset total
    st.session_state.reset_key += 1
    # Hapus data lain di session state jika ada
    st.rerun()

# 2. FUNGSI AMBIL DATA GOOGLE SHEETS
@st.cache_data(ttl=300)
def get_blacklist_data(sheet_url):
    try:
        if not sheet_url or "google.com" not in sheet_url:
            return []
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').split('/edit')[0] + '/export?format=csv'
        blacklist_df = pd.read_csv(csv_url)
        if 'TicketNo' in blacklist_df.columns:
            return blacklist_df['TicketNo'].astype(str).str.strip().unique().tolist()
        return []
    except:
        return []

st.title("📲 Pro WO Reporter")

# --- MASUKKAN LINK GOOGLE SHEETS ANDA DI SINI ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mhdwIlP20HmtmlYb0BP-vfH32jiE82m5GGq6_yCaYSk/edit?gid=758149661#gid=758149661"

blacklist_tickets = get_blacklist_data(GOOGLE_SHEET_URL)

# File Uploader dengan Key Dinamis (Solusi Tombol Reset)
uploaded_files = st.file_uploader(
    "Upload file WO History", 
    type=['xlsx', 'csv'], 
    accept_multiple_files=True, 
    key=f"uploader_{st.session_state.reset_key}"
)

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

        # FILTER DATA PEMBANDING (TicketNo)
        if 'TicketNo' in df.columns and blacklist_tickets:
            df['TicketNo_Str'] = df['TicketNo'].astype(str).str.strip()
            initial_count = len(df)
            # Menghilangkan data yang ada di blacklist
            df = df[~df['TicketNo_Str'].isin(blacklist_tickets)]
            removed = initial_count - len(df)
            if removed > 0:
                st.sidebar.info(f"🚫 {removed} Tiket Pembanding disembunyikan")

        # FILTER WORK ACTIVITY
        if 'WorkActivity' in df.columns:
            all_activities = sorted(df['WorkActivity'].unique().astype(str))
            selected_activities = st.multiselect("Pilih WorkActivity:", options=all_activities, default=all_activities)
            df = df[df['WorkActivity'].isin(selected_activities)]

        # TOMBOL RESET (DIPERBAIKI)
        if st.button("🔄 MULAI DARI AWAL"):
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
        else:
            st.warning("Data kosong setelah difilter.")
            
    except Exception as e:
        st.error(f"Error: {e}")
        if st.button("Reset Sistem"):
            reset_app()
