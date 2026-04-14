import streamlit as st
import pandas as pd
import datetime
from urllib.parse import quote


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
    .mega-download-btn {
        display: block; text-align: center; padding: 15px; background-color: #d32f2f; color: white !important; 
        text-decoration: none; border-radius: 10px; font-size: 16px; font-weight: bold; width: 100%; border: none;
    }
    </style>
    """, unsafe_allow_html=True)


try:
    GOOGLE_SHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ URL Google Sheets belum diatur di menu Secrets!")
    st.stop()

@st.cache_data(ttl=300)
def get_blacklist_data(sheet_url):
    try:
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').split('/edit')[0] + '/export?format=csv'
        df_b = pd.read_csv(csv_url)
        return df_b['TicketNo'].astype(str).str.strip().unique().tolist()
    except: return []

# 3. LOGIKA DOWNLOAD
def get_report_urls():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return [
        f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled",
        f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked",
        f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"
    ]

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

st.title("📲 Monitoring WO Real-time")


urls = get_report_urls()
js_code = f"""
    <script>
    function downloadAll() {{
        const urls = {urls};
        urls.forEach(url => window.open(url, '_blank'));
    }}
    </script>
    <button onclick="downloadAll()" class="mega-download-btn">🚀 DOWNLOAD 3 DATA SEKALIGUS</button>
"""
st.markdown(js_code, unsafe_allow_html=True)
st.markdown('<a href="file:///C:/Users/User/Downloads" style="color:#f57c00; font-size:12px;">📂 Buka Folder Downloads (PC)</a>', unsafe_allow_html=True)

st.markdown("---")

# SEKSI 2: PROSES
blacklist = get_blacklist_data(GOOGLE_SHEET_URL)
uploaded_files = st.file_uploader("2. Upload/Tempel file:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
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
