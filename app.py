import streamlit as st
import pandas as pd
import datetime
import pytz
from urllib.parse import quote

# 1. SETTING TAMPILAN
st.set_page_config(page_title="WO Reporter SLA Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #1565c0; background-color: #e3f2fd; }
    header, footer {visibility: hidden;}
    p, span, label, div { color: black !important; }
    
    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }
    .sla-tag { color: #d32f2f; font-weight: bold; } /* Warna merah untuk jam SLA */
    
    .download-btn { 
        display: block; text-align: center; padding: 10px; background-color: #2e7d32; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIKA ZONA WAKTU ---
tz_jkt = pytz.timezone('Asia/Jakarta')
now_jkt = datetime.datetime.now(tz_jkt)
today_date = now_jkt.date()

st.title("📲 Monitoring WO & SLA Real-time")

# --- SEKSI PILIH TANGGAL ---
st.subheader("Rentang Tanggal SLA")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Dari:", today_date.replace(day=1))
with col2:
    end_date = st.date_input("Sampai:", today_date)

def get_report_urls(d_from, d_to):
    f_from = d_from.strftime("%d-%b-%Y")
    f_to = d_to.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    
    return {
        f"📥 DOWNLOAD SCHEDULED": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Scheduled",
        f"📥 DOWNLOAD BOOKED": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Booked",
        f"📥 DOWNLOAD ON PROGRESS": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=On%20Progress"
    }

# --- LANGKAH 1 ---
links = get_report_urls(start_date, end_date)
for name, url in links.items():
    st.markdown(f'<a href="{url}" target="_blank" class="download-btn">{name}</a>', unsafe_allow_html=True)

st.markdown("---")

# --- LANGKAH 2 ---
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader("Upload file WO:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            df_temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            df_temp.columns = [c.strip() for c in df_temp.columns]
            dfs.append(df_temp)
        
        df = pd.concat(dfs, ignore_index=True)

        if 'WorkActivity' in df.columns:
            list_activity = sorted(df['WorkActivity'].unique().astype(str))
            selected_activity = st.multiselect("Filter Activity:", options=list_activity, default=list_activity)
            df = df[df['WorkActivity'].isin(selected_activity)]

        if st.button("🗑️ RESET APLIKASI"):
            st.session_state.reset_key += 1
            st.rerun()

        st.markdown("---")
        
        if not df.empty:
            # 1. KONVERSI KE DATETIME LENGKAP (TANGGAL + JAM)
            df['ActualTargetDate_DT'] = pd.to_datetime(df['ActualTargetDate'])
            
            # 2. SORTING BERDASARKAN WAKTU (Tiket paling awal muncul pertama)
            df = df.sort_values(['EngineerName', 'ActualTargetDate_DT', 'MerchantName'])
            
            res_txt = ""
            for eng, g_eng in df.groupby('EngineerName'):
                h = str(eng).upper()
                st.markdown(f"<p class='engineer-header'>{h}</p>", unsafe_allow_html=True)
                res_txt += f"*{h}*\n"
                
                # Grouping per tanggal (tanpa jam untuk header tanggal)
                g_eng['Date_Only'] = g_eng['ActualTargetDate_DT'].dt.date
                for date_only, g_dt in g_eng.groupby('Date_Only'):
                    
                    # Logika Simbol Tanggal
                    if date_only < today_date:
                        sym = "🔴"
                    elif date_only == today_date:
                        sym = "🗓️"
                    else:
                        sym = "🟡"
                    
                    date_header_str = f"{sym} {date_only.strftime('%d-%m-%Y')}"
                    st.markdown(f"<p class='date-header'>{date_header_str}</p>", unsafe_allow_html=True)
                    res_txt += f"{date_header_str}\n"
                    
                    for _, r in g_dt.iterrows():
                        # 3. AMBIL JAM SLA (HH:mm)
                        jam_sla = r['ActualTargetDate_DT'].strftime('%H:%M')
                        
                        row_display = f"• {r['MerchantName']} - {r['WorkActivity']} [<span class='sla-tag'>{jam_sla}</span>]"
                        row_wa = f"• {r['MerchantName']} - {r['WorkActivity']} ({jam_sla})"
                        
                        st.markdown(f"<p class='item-list'>{row_display}</p>", unsafe_allow_html=True)
                        res_txt += f"{row_wa}\n"
                res_txt += "\n"

            st.text_area("📋 Hasil Rekap (SLA Presisi):", value=res_txt, height=250)

    except Exception as e:
        st.error(f"Gagal memproses file: {str(e)}")
