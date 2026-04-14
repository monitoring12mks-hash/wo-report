import streamlit as st
import pandas as pd
import datetime
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
    
    /* Tombol Download Utama */
    .mega-download-btn {
        display: block; text-align: center; padding: 15px; 
        background-color: #d32f2f; color: white !important; 
        text-decoration: none; border-radius: 10px; 
        font-size: 16px; font-weight: bold; margin-bottom: 10px;
        border: none; cursor: pointer; width: 100%;
    }
    .mega-download-btn:hover { background-color: #b71c1c; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIKA URL (Script Anda)
def get_report_urls():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    
    urls = [
        f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled",
        f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked",
        f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"
    ]
    return urls

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

st.title("📲 Monitoring WO Real-time")

# --- SEKSI 1: SINGLE DOWNLOAD BUTTON ---
st.subheader("1. Download Semua Data")
urls = get_report_urls()

# JavaScript untuk mendownload banyak file sekaligus
js_code = f"""
    <script>
    function downloadAll() {{
        const urls = {urls};
        urls.forEach((url, index) => {{
            setTimeout(() => {{
                const link = document.createElement('a');
                link.href = url;
                link.target = '_blank';
                link.download = '';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}, index * 1000); // Jeda 1 detik antar download agar tidak diblokir browser
        }});
    }}
    </script>
    <button onclick="downloadAll()" class="mega-download-btn">🚀 DOWNLOAD 3 DATA SEKALIGUS</button>
"""
st.markdown(js_code, unsafe_allow_html=True)
st.caption("⚠️ Jika muncul peringatan 'Allow multiple downloads', klik **Allow/Izinkan**.")

# Tombol Folder (Tetap disediakan untuk akses cepat)
st.markdown('<a href="file:///C:/Users/User/Downloads" style="text-decoration:none; color:#f57c00; font-size:12px; font-weight:bold;">📂 Buka Folder Downloads (PC)</a>', unsafe_allow_html=True)

st.markdown("---")

# --- SEKSI 2: PENGOLAHAN DATA ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mhdwIlP20HmtmlYb0BP-vfH32jiE82m5GGq6_yCaYSk/edit?gid=758149661#gid=758149661"

uploaded_files = st.file_uploader(
    "2. Masukkan File ke sini:", 
    type=['xlsx', 'csv'], 
    accept_multiple_files=True, 
    key=f"up_{st.session_state.reset_key}"
)

# (Logika pengolahan data tetap sama seperti sebelumnya...)
if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            df_temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            df_temp.columns = [c.strip() for c in df_temp.columns]
            dfs.append(df_temp)
        
        df = pd.concat(dfs, ignore_index=True)

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

            st.text_area("📋 Hasil Laporan:", value=res_txt, height=200)

    except Exception as e:
        st.error("Gagal memproses file.")
