import streamlit as st
import pandas as pd
import datetime
import pytz
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
    
    .download-btn { 
        display: block; text-align: center; padding: 10px; background-color: #2e7d32; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIKA ZONA WAKTU ---
tz_jkt = pytz.timezone('Asia/Jakarta')
now_jkt = datetime.datetime.now(tz_jkt).date()

st.title("📲 Monitoring WO Real-time")

# --- SEKSI PILIH TANGGAL (RANGE) ---
st.subheader("Pilih Rentang Tanggal Download")
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Dari Tanggal:", now_jkt.replace(day=1))
with col2:
    end_date = st.date_input("Sampai Tanggal:", now_jkt)

def get_report_urls(d_from, d_to):
    # Format sesuai kebutuhan VCare (01-Apr-2026)
    f_from = d_from.strftime("%d-%b-%Y")
    f_to = d_to.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    
    return {
        f"📥 DOWNLOAD SCHEDULED ({f_to})": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Scheduled",
        f"📥 DOWNLOAD BOOKED ({f_to})": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Booked",
        f"📥 DOWNLOAD ON PROGRESS ({f_to})": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(date_to if 'date_to' in locals() else f_to)}&WorkActivity=On%20Progress"
    }

# --- LANGKAH 1 ---
st.subheader("Langkah 1: Download Data")
links = get_report_urls(start_date, end_date)
for name, url in links.items():
    st.markdown(f'<a href="{url}" target="_blank" class="download-btn">{name}</a>', unsafe_allow_html=True)

st.markdown("---")

# --- LANGKAH 2 ---
st.subheader("Langkah 2: Upload & Gabung")

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader(
    "Tarik file ke sini:", 
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

        # Filter Work Activity
        if 'WorkActivity' in df.columns:
            list_activity = sorted(df['WorkActivity'].unique().astype(str))
            selected_activity = st.multiselect("Filter Activity:", options=list_activity, default=list_activity)
            df = df[df['WorkActivity'].isin(selected_activity)]

        if st.button("🗑️ RESET APLIKASI"):
            st.session_state.reset_key += 1
            st.rerun()

        st.markdown("---")
        
        if not df.empty:
            df['ActualTargetDate_DT'] = pd.to_datetime(df['ActualTargetDate'])
            df['ActualTargetDate_STR'] = df['ActualTargetDate_DT'].dt.strftime('%Y-%m-%d')
            df = df.sort_values(['EngineerName', 'ActualTargetDate_DT', 'MerchantName'])
            
            res_txt = ""
            for eng, g_eng in df.groupby('EngineerName'):
                h = str(eng).upper()
                st.markdown(f"<p class='engineer-header'>{h}</p>", unsafe_allow_html=True)
                res_txt += f"*{h}*\n"
                
                for dt_str, g_dt in g_eng.groupby('ActualTargetDate_STR'):
                    current_dt = g_dt['ActualTargetDate_DT'].iloc[0].date()
                    
                    # Logika Simbol
                    if current_dt < now_jkt:
                        sym = "🔴" # Lewat
                    elif current_dt == now_jkt:
                        sym = "🗓️" # Hari ini
                    else:
                        sym = "🟡" # Besok/Lusa
                    
                    date_label = f"{sym} {current_dt.strftime('%d-%m-%Y')}"
                    st.markdown(f"<p class='date-header'>{date_label}</p>", unsafe_allow_html=True)
                    res_txt += f"{date_label}\n"
                    
                    for _, r in g_dt.iterrows():
                        row_txt = f"• {r['MerchantName']} - {r['WorkActivity']}"
                        st.markdown(f"<p class='item-list'>{row_txt}</p>", unsafe_allow_html=True)
                        res_txt += f"{row_txt}\n"
                res_txt += "\n"

            st.text_area("📋 Hasil (Siap di-Copy):", value=res_txt, height=200)

    except Exception as e:
        st.error("Gagal memproses file.")
