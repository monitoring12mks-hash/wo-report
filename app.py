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
    
    /* Tombol Download */
    .download-btn { 
        display: block; text-align: center; padding: 10px; background-color: #2e7d32; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 8px;
    }
    /* Tombol Buka Folder */
    .folder-btn { 
        display: block; text-align: center; padding: 10px; background-color: #f57c00; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 20px;
        border: 2px solid #e65100;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIKA URL VCARE
def get_report_urls():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return {
        "📥 DOWNLOAD SCHEDULED": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled",
        "📥 DOWNLOAD BOOKED": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked",
        "📥 DOWNLOAD ON PROGRESS": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"
    }

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def full_reset():
    st.session_state.reset_key += 1
    st.rerun()

# --- UI UTAMA ---
st.title("📲 Monitoring WO Real-time")

# SEKSI 1: DOWNLOAD & CLEANUP
st.subheader("Langkah 1: Ambil Data & Kelola File")
links = get_report_urls()
for name, url in links.items():
    st.markdown(f'<a href="{url}" target="_blank" class="download-btn">{name}</a>', unsafe_allow_html=True)

# TOMBOL KE FOLDER DOWNLOAD
# Catatan: Protokol 'file:///' bekerja berbeda-beda tiap OS/Browser
st.markdown('<a href="file:///C:/Users/User/Downloads" class="folder-btn">📂 BUKA FOLDER DOWNLOAD (PC/LAPTOP)</a>', unsafe_allow_html=True)
st.caption("Catatan: Jika tombol folder tidak terbuka otomatis (karena proteksi browser), silakan buka folder 'Downloads' manual di HP/PC Anda untuk menghapus file lama.")

st.markdown("---")

# SEKSI 2: UPLOAD & REPORT
st.subheader("Langkah 2: Upload & Gabung")
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mhdwIlP20HmtmlYb0BP-vfH32jiE82m5GGq6_yCaYSk/edit?gid=758149661#gid=758149661"

uploaded_files = st.file_uploader(
    "Tarik file ke sini:", 
    type=['xlsx', 'csv'], 
    accept_multiple_files=True, 
    key=f"up_{st.session_state.reset_key}"
)

if uploaded_files:
    try:
        # (Logika pengolahan data sama seperti sebelumnya)
        dfs = []
        for f in uploaded_files:
            df_temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            df_temp.columns = [c.strip() for c in df_temp.columns]
            dfs.append(df_temp)
        
        df = pd.concat(dfs, ignore_index=True)

        # Logika Filter & Tampilan
        if st.button("🗑️ RESET APLIKASI"):
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

            st.text_area("📋 Hasil (Siap di-Copy):", value=res_txt, height=200)

    except Exception as e:
        st.error(f"Gagal memproses file.")
