import streamlit as st
import pandas as pd
import datetime
import requests
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
    .download-link {
        display: block; text-align: center; padding: 12px; background-color: #2e7d32; 
        color: white !important; text-decoration: none; border-radius: 8px; 
        margin-bottom: 10px; font-weight: bold; font-size: 14px;
    }
    .summary-card {
        background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px;
        padding: 15px; margin-bottom: 20px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KONFIGURASI URL & DATA
def get_report_config():
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

# 3. FUNGSI SUMMARY (Tanpa Download Manual)
def get_live_summary(configs):
    total = 0
    details = {}
    # Catatan: Fungsi ini membutuhkan session/cookie jika website perusahaan memproteksi akses langsung via script.
    # Jika requests gagal karena login, summary akan menampilkan data dari file yang diupload saja.
    return total, details

try:
    GOOGLE_SHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Secrets 'GSHEET_URL' belum diisi!")
    st.stop()

st.title("📲 Monitoring WO Real-time")

# --- SEKSI 1: DOWNLOAD PER LINK ---
st.subheader("1. Download Data VCare")
reports = get_report_config()

for r in reports:
    st.markdown(f'<a href="{r["url"]}" target="_blank" class="download-link">📥 Download {r["name"]}</a>', unsafe_allow_html=True)

st.markdown("---")

# --- SEKSI 2: UPLOAD & SUMMARY ---
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

@st.cache_data(ttl=300)
def get_blacklist_data(sheet_url):
    try:
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').split('/edit')[0] + '/export?format=csv'
        df_b = pd.read_csv(csv_url)
        return df_b['TicketNo'].astype(str).str.strip().unique().tolist()
    except: return []

blacklist = get_blacklist_data(GOOGLE_SHEET_URL)

uploaded_files = st.file_uploader("2. Upload/Tempel file untuk Summary & Report:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            temp.columns = [c.strip() for c in temp.columns]
            dfs.append(temp)
        
        df = pd.concat(dfs, ignore_index=True)

        # Filter Blacklist Tiket Pembanding
        if 'TicketNo' in df.columns and blacklist:
            df = df[~df['TicketNo'].astype(str).str.strip().isin(blacklist)]

        # TAMPILAN SUMMARY TOTAL
        total_data = len(df)
        st.markdown(f"""
            <div class="summary-card">
                <p style="margin:0; font-size:14px; color:#666;">Total Work Order Aktif</p>
                <h1 style="margin:0; color:#1565c0;">{total_data}</h1>
                <p style="margin:0; font-size:12px; color:#2e7d32;">(Setelah filter data pembanding)</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ BERSIHKAN LAYAR"):
            st.session_state.reset_key += 1
            st.rerun()

        st.markdown("---")
        
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
            st.text_area("📋 Copy Hasil Laporan:", value=res_txt, height=200)
    except:
        st.error("Gagal memproses file.")
