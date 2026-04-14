import streamlit as st
import pandas as pd
import datetime
import time
from urllib.parse import quote

# 1. SETTING TAMPILAN
st.set_page_config(page_title="WO Reporter Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #1565c0; background-color: #e3f2fd; }
    header, footer {visibility: hidden;}
    p, span, label, div { color: black !important; }
    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIKA URL VCARE
def get_report_data():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    
    return [
        {"name": "Scheduled", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled"},
        {"name": "Booked", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked"},
        {"name": "On Progress", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"}
    ]

# 3. AMBIL SECRETS
try:
    GOOGLE_SHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Konfigurasi Secrets 'GSHEET_URL' tidak ditemukan!")
    st.stop()

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

st.title("📲 Monitoring WO Real-time")

# --- SEKSI 1: DOWNLOAD DENGAN ANIMASI SEKUENSIAL ---
st.subheader("1. Download Data VCare")

reports = get_report_data()

if st.button("🚀 MULAI DOWNLOAD BERURUTAN", use_container_width=True):
    progress_text = st.empty()
    bar = st.progress(0)
    
    for i, report in enumerate(reports):
        # Update UI seolah-olah sedang memproses
        progress_text.info(f"Mempersiapkan download: **{report['name']}**...")
        
        # Animasi loading singkat per file
        for percent in range(100):
            time.sleep(0.01)
            bar.progress((i * 33) + int(percent / 3))
        
        # Trigger download menggunakan JavaScript di tab baru
        st.markdown(f"""
            <script>
                window.open('{report['url']}', '_blank');
            </script>
        """, unsafe_allow_html=True)
        
        time.sleep(1.5)  # Jeda jeda agar browser tidak menganggap spam
    
    bar.progress(100)
    progress_text.success("Semua permintaan download telah dikirim ke browser!")

st.caption("💡 Jika download tidak jalan, pastikan izin 'Pop-up' di browser HP sudah **Allowed**.")
st.markdown("---")

# --- SEKSI 2: PENGOLAHAN DATA ---
@st.cache_data(ttl=300)
def get_blacklist_data(sheet_url):
    try:
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').split('/edit')[0] + '/export?format=csv'
        df_b = pd.read_csv(csv_url)
        return df_b['TicketNo'].astype(str).str.strip().unique().tolist()
    except: return []

blacklist = get_blacklist_data(GOOGLE_SHEET_URL)
uploaded_files = st.file_uploader("2. Upload file hasil download:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            temp.columns = [c.strip() for c in temp.columns]
            dfs.append(temp)
        
        df = pd.concat(dfs, ignore_index=True)

        # Filter Blacklist
        if 'TicketNo' in df.columns and blacklist:
            df = df[~df['TicketNo'].astype(str).str.strip().isin(blacklist)]

        if st.button("🗑️ BERSIHKAN LAYAR"):
            st.session_state.reset_key += 1
            st.rerun()

        if not df.empty:
            if 'ActualTargetDate' in df.columns:
                df['ActualTargetDate'] = pd.to_datetime(df['ActualTargetDate']).dt.strftime('%Y-%m-%d')
            
            df = df.sort_values(['EngineerName', 'ActualTargetDate', 'MerchantName'])
            res_txt = ""
            for eng, g_eng in df.groupby('EngineerName'):
                h = str(eng).upper()
                st.markdown(f"<p class='engineer-header'>{h}</p>", unsafe_allow_html=True)
                res_txt += f"*{h}*\n"
                for dt, g_dt in g_eng.groupby('ActualTargetDate'):
                    d_l = f"📅 {dt}"
                    st.markdown(f"<p class='date-header'>{d_l}</p>", unsafe_allow_html=True)
                    res_txt += f"{d_l}\n"
                    for _, r in g_dt.iterrows():
                        row_txt = f"• {r['MerchantName']} - {r['WorkActivity']}"
                        st.markdown(f"<p class='item-list'>{row_txt}</p>", unsafe_allow_html=True)
                        res_txt += f"{row_txt}\n"
                res_txt += "\n"
            st.text_area("📋 Copy Hasil:", value=res_txt, height=200)
    except:
        st.error("Gagal memproses file. Pastikan kolom sesuai.")
