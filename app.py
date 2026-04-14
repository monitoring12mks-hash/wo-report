import streamlit as st
import pandas as pd
import datetime
from urllib.parse import quote

# 1. SETTING TAMPILAN (Tetap Putih & Bersih)
st.set_page_config(page_title="WO Reporter Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #2e7d32; background-color: #f1f8e9; }
    header, footer {visibility: hidden;}
    p, span, label, div { color: black !important; }
    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }
    .download-btn { 
        display: block; text-align: center; padding: 10px; background-color: #1565c0; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 10px;
    }
    .delete-info { font-size: 11px; color: #d32f2f !important; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIKA URL (Sesuai Script Anda)
def get_report_urls():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return {
        "1. DOWNLOAD SCHEDULED": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled",
        "2. DOWNLOAD BOOKED": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked",
        "3. DOWNLOAD ON PROGRESS": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"
    }

@st.cache_data(ttl=300)
def get_blacklist_data(sheet_url):
    try:
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').split('/edit')[0] + '/export?format=csv'
        df_b = pd.read_csv(csv_url)
        return df_b['TicketNo'].astype(str).str.strip().unique().tolist() if 'TicketNo' in df_b.columns else []
    except: return []

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def full_reset():
    st.session_state.reset_key += 1
    st.rerun()

# --- UI UTAMA ---
st.title("📲 Monitoring WO Per Jam")

# Kolom Download
st.info("💡 Login VCare dulu di tab sebelah sebelum klik tombol di bawah.")
links = get_report_urls()
for name, url in links.items():
    st.markdown(f'<a href="{url}" target="_blank" class="download-btn">{name}</a>', unsafe_allow_html=True)

st.markdown('<p class="delete-info">⚠️ Ingat: Hapus file di folder Downloads HP Anda secara manual setiap selesai report agar memori tidak penuh.</p>', unsafe_allow_html=True)

st.markdown("---")

# Bagian Pengolahan
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mhdwIlP20HmtmlYb0BP-vfH32jiE82m5GGq6_yCaYSk/edit?gid=758149661#gid=758149661"
blacklist = get_blacklist_data(GOOGLE_SHEET_URL)

uploaded_files = st.file_uploader(
    "📥 Tempel/Upload file di sini:", 
    type=['xlsx', 'csv'], 
    accept_multiple_files=True, 
    key=f"up_{st.session_state.reset_key}"
)

if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            df_temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            df_temp.columns = [c.strip() for c in df_temp.columns]
            dfs.append(df_temp)
        
        df = pd.concat(dfs, ignore_index=True)

        # Filter Blacklist
        if 'TicketNo' in df.columns and blacklist:
            df = df[~df['TicketNo'].astype(str).str.strip().isin(blacklist)]

        # Filter Activity Manual
        if 'WorkActivity' in df.columns:
            acts = sorted(df['WorkActivity'].unique().astype(str))
            sel_acts = st.multiselect("Filter Tampilan:", acts, default=acts)
            df = df[df['WorkActivity'].isin(sel_acts)]

        # Tombol Reset UI
        if st.button("🗑️ BERSIHKAN LAYAR & MULAI ULANG"):
            full_reset()

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

            st.text_area("📋 Copy untuk WhatsApp:", value=res_txt, height=200)
            
    except Exception as e:
        st.error(f"Gagal memproses file. Pastikan format benar.")
