import streamlit as st
import pandas as pd
import datetime
from urllib.parse import quote

# 1. KONFIGURASI TAMPILAN (Mobile Friendly)
st.set_page_config(page_title="WO Monitor Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    header, footer {visibility: hidden;}
    .download-card {
        border: 1px solid #e0e0e0; border-radius: 10px; padding: 12px;
        margin-bottom: 10px; background-color: #f9f9f9;
    }
    .btn-link {
        display: block; text-align: center; padding: 10px;
        background-color: #1565c0; color: white !important;
        text-decoration: none; border-radius: 5px; font-weight: bold;
    }
    .summary-box {
        background-color: #e3f2fd; border: 1px solid #1565c0;
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIKA URL VCARE
def get_vcare_links():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return [
        {"label": "📅 Scheduled", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled"},
        {"label": "📑 Booked", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked"},
        {"label": "⏳ On Progress", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"}
    ]

# 3. KEAMANAN DATA (SECRETS)
try:
    GSHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ URL GSheet belum diatur di menu Secrets Streamlit!")
    st.stop()

@st.cache_data(ttl=300)
def get_blacklist():
    try:
        csv_url = GSHEET_URL.replace('/edit?usp=sharing', '/export?format=csv').split('/edit')[0] + '/export?format=csv'
        db = pd.read_csv(csv_url)
        return db['TicketNo'].astype(str).str.strip().unique().tolist()
    except: return []

# --- UI UTAMA ---
st.title("📊 WO Live Monitor")

# SEKSI 1: DOWNLOAD
st.subheader("1. Download Data")
for item in get_vcare_links():
    st.markdown(f"""
        <div class="download-card">
            <div style="font-weight:bold; margin-bottom:5px;">{item['label']}</div>
            <a href="{item['url']}" target="_blank" class="btn-link">Download File</a>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# SEKSI 2: UPLOAD & SUMMARY
st.subheader("2. Upload & Summary")
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader("Upload file hasil download:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            temp.columns = [c.strip() for c in temp.columns]
            dfs.append(temp)
        
        df = pd.concat(dfs, ignore_index=True)
        
        # Filter Blacklist
        blacklist = get_blacklist()
        if 'TicketNo' in df.columns and blacklist:
            df = df[~df['TicketNo'].astype(str).str.strip().isin(blacklist)]
        
        # TAMPILAN SUMMARY
        st.markdown(f"""
            <div class="summary-box">
                <small>Total WO Aktif (Setelah Filter)</small>
                <h1 style="margin:0; color:#1565c0;">{len(df)}</h1>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Reset Per Jam"):
            st.session_state.reset_key += 1
            st.rerun()

        # REKAP TEXT UNTUK WHATSAPP
        if not df.empty:
            if 'ActualTargetDate' in df.columns:
                df['ActualTargetDate'] = pd.to_datetime(df['ActualTargetDate']).dt.strftime('%d-%m-%Y')
            
            df = df.sort_values(['EngineerName', 'ActualTargetDate'])
            
            wa_text = ""
            for eng, g_eng in df.groupby('EngineerName'):
                wa_text += f"*{str(eng).upper()}*\n"
                for dt, g_dt in g_eng.groupby('ActualTargetDate'):
                    wa_text += f"📅 {dt}\n"
                    for _, r in g_dt.iterrows():
                        wa_text += f"• {r['MerchantName']} - {r['WorkActivity']}\n"
                wa_text += "\n"
            
            st.text_area("📋 Salin untuk WA:", value=wa_text, height=150)
            
    except Exception as e:
        st.error("Gagal memproses. Pastikan file sesuai format VCare.")
