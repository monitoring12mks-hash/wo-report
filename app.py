import streamlit as st
import pandas as pd
import datetime
import pytz
from urllib.parse import quote

# 1. SETTING TAMPILAN
st.set_page_config(page_title="WO Reporter SLA", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    header, footer {visibility: hidden;}
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #1565c0; background-color: #f0f7ff; }
    p, span, label, div { color: black !important; }
    
    /* Style Tombol Download Satuan */
    .btn-download { 
        display: block; text-align: center; padding: 12px; background-color: #2e7d32; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 10px;
    }
    .btn-download:hover { background-color: #1b5e20; }
    
    /* Style untuk Laporan */
    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }
    .sla-tag { color: #d32f2f; font-weight: bold; }
    
    .info-box {
        background-color: #e3f2fd; border-left: 5px solid #1565c0;
        padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIKA ZONA WAKTU ---
tz_jkt = pytz.timezone('Asia/Jakarta')
now_jkt = datetime.datetime.now(tz_jkt)
today_date = now_jkt.date()

st.title("📲 Monitoring WO Real-time")

# --- SWITCHER MODE ---
# Meskipun fungsinya sekarang sama (satuan), switcher tetap ada jika Anda ingin membedakan instruksi visual
mode = st.radio("Pilih Mode Perangkat:", ["📱 Mobile", "💻 PC / Laptop"], horizontal=True)

st.markdown("---")

# --- RENTANG TANGGAL ---
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Dari:", today_date.replace(day=1))
with col2:
    end_date = st.date_input("Sampai:", today_date)

def get_links(d_from, d_to):
    f_from = d_from.strftime("%d-%b-%Y")
    f_to = d_to.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return {
        "Scheduled": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Scheduled",
        "Booked": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Booked",
        "On Progress": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=On%20Progress"
    }

links = get_links(start_date, end_date)

# --- SEKSI DOWNLOAD (SATU PER SATU) ---
st.subheader("Langkah 1: Download File (Satu per Satu)")

if mode == "💻 PC / Laptop":
    st.markdown("""
        <div class="info-box">
            <b>Tips PC Mode:</b><br>
            Klik tombol di bawah satu per satu. Browser akan menanyakan lokasi penyimpanan jika Anda mengaktifkan 
            <i>"Ask where to save each file"</i> di pengaturan browser.
        </div>
    """, unsafe_allow_html=True)

# Menampilkan tombol download satu per satu untuk semua mode
for name, url in links.items():
    st.markdown(f'<a href="{url}" target="_blank" class="btn-download">📥 DOWNLOAD {name.upper()}</a>', unsafe_allow_html=True)

st.markdown("---")

# --- LANGKAH 2: UPLOAD & REKAP ---
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader("Langkah 2: Upload Hasil Download", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            df_temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            df_temp.columns = [c.strip() for c in df_temp.columns]
            dfs.append(df_temp)
        
        df = pd.concat(dfs, ignore_index=True)

        if 'WorkActivity' in df.columns:
            list_act = sorted(df['WorkActivity'].unique().astype(str))
            sel_act = st.multiselect("Filter Activity:", options=list_act, default=list_act)
            df = df[df['WorkActivity'].isin(sel_act)]

        if st.button("🗑️ RESET APLIKASI"):
            st.session_state.reset_key += 1
            st.rerun()

        if not df.empty:
            # Pastikan kolom tanggal menyertakan jam untuk SLA
            df['ActualTargetDate_DT'] = pd.to_datetime(df['ActualTargetDate'])
            df = df.sort_values(['EngineerName', 'ActualTargetDate_DT', 'MerchantName'])
            
            res_txt = ""
            nama_hari = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}

            for eng, g_eng in df.groupby('EngineerName'):
                h = str(eng).upper()
                st.markdown(f"<p class='engineer-header'>{h}</p>", unsafe_allow_html=True)
                res_txt += f"*{h}*\n"
                
                g_eng['Date_Only'] = g_eng['ActualTargetDate_DT'].dt.date
                for date_only, g_dt in g_eng.groupby('Date_Only'):
                    # Logika Simbol
                    if date_only < today_date: sym = "🔴"
                    elif date_only == today_date: sym = "🗓️"
                    else: sym = "🟡"
                    
                    hari_indo = nama_hari.get(date_only.strftime('%A'))
                    date_header = f"{sym} {hari_indo}, {date_only.strftime('%d-%m-%Y')}"
                    
                    st.markdown(f"<p class='date-header'>{date_header}</p>", unsafe_allow_html=True)
                    res_txt += f"{date_header}\n"
                    
                    for _, r in g_dt.iterrows():
                        jam = r['ActualTargetDate_DT'].strftime('%H:%M')
                        line_display = f"• {r['MerchantName']} - {r['WorkActivity']} [<span class='sla-tag'>{jam}</span>]"
                        line_wa = f"• {r['MerchantName']} - {r['WorkActivity']} ({jam})"
                        
                        st.markdown(f"<p class='item-list'>{line_display}</p>", unsafe_allow_html=True)
                        res_txt += f"{line_wa}\n"
                res_txt += "\n"

            st.text_area("📋 Hasil (Siap di-Copy):", value=res_txt, height=250)

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
