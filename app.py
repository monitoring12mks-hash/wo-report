import streamlit as st
import pandas as pd
import datetime
import pytz
from urllib.parse import quote

# 1. KONFIGURASI HALAMAN & CSS
st.set_page_config(page_title="WO Reporter SLA Pro", layout="centered")

st.markdown("""
    <style>
    /* 1. Menghilangkan Header, Footer, dan Menu Hamburger */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}

    /* 2. Menghilangkan tombol 'Manage app' secara paksa */
    /* Target berdasarkan posisi dan elemen fungsional Streamlit Cloud */
    [data-testid="manage-app-button"], 
    .stApp > div:last-child > div:last-child {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 3. Menghilangkan elemen status/viewer di pojok kanan bawah */
    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    /* Styling Standar Aplikasi */
    .stApp { background-color: white; color: black; }
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #1565c0; background-color: #f0f7ff; }
    p, span, label, div { color: black !important; }
    
    .btn-download { 
        display: block; text-align: center; padding: 12px; background-color: #2e7d32; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 10px;
    }
    .btn-download:hover { background-color: #1b5e20; opacity: 0.9; }
    
    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }
    
    .info-box {
        background-color: #e3f2fd; border-left: 5px solid #1565c0;
        padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIKA ZONA WAKTU (WIB)
tz_jkt = pytz.timezone('Asia/Jakarta')
now_jkt = datetime.datetime.now(tz_jkt)
today_date = now_jkt.date()

# 3. AMBIL SECRETS
try:
    GOOGLE_SHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Secrets 'GSHEET_URL' tidak ditemukan di Streamlit Cloud!")
    st.stop()

# --- FUNGSI DOWNLOADER ---
def get_links(d_from, d_to):
    f_from = d_from.strftime("%d-%b-%Y")
    f_to = d_to.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return {
        "Assigning": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Assigning",
        "Scheduled": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Scheduled",
        "Booked": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Booked",
        "On Progress": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=On%20Progress"
    }

# --- UI UTAMA ---
st.title("📲 WO Monitoring & SLA")

device_mode = st.radio("Pilih Mode Perangkat:", ["📱 Mobile", "💻 PC / Laptop"], horizontal=True)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Dari Tanggal:", today_date.replace(day=1))
with col2:
    end_date = st.date_input("Sampai Tanggal:", today_date)

links = get_links(start_date, end_date)

st.subheader("Langkah 1: Download Data")
if device_mode == "💻 PC / Laptop":
    st.markdown('<div class="info-box"><b>💻 MODE PC AKTIF</b><br>Klik tombol satu per satu dan tentukan folder penyimpanan Anda.</div>', unsafe_allow_html=True)

for name, url in links.items():
    st.markdown(f'<a href="{url}" target="_blank" class="btn-download">📥 DOWNLOAD {name.upper()}</a>', unsafe_allow_html=True)

st.markdown("---")

# SEKSI UPLOAD & PROSES
st.subheader("Langkah 2: Upload & Rekap")

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader("Upload file Excel/CSV:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    try:
        # A. LOAD BLACKLIST
        @st.cache_data(ttl=300)
        def get_blacklist():
            try:
                sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                db = pd.read_csv(csv_url)
                return db['TicketNo'].astype(str).str.strip().unique().tolist()
            except:
                return []

        blacklist_tickets = get_blacklist()

        # B. GABUNG FILE
        dfs = []
        for f in uploaded_files:
            temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            temp.columns = [c.strip() for c in temp.columns]
            dfs.append(temp)

        df = pd.concat(dfs, ignore_index=True)
        
        # Penanganan khusus status Assigning yang mungkin kosong
        if 'EngineerName' in df.columns:
            df['EngineerName'] = df['EngineerName'].fillna("BELUM DI-ASSIGN")
        if 'ActualTargetDate' in df.columns:
            df['ActualTargetDate'] = df['ActualTargetDate'].fillna(now_jkt.strftime("%Y-%m-%d %H:%M:%S"))

        # C. FILTER BLACKLIST
        if not df.empty and 'TicketNo' in df.columns:
            initial_len = len(df)
            df = df[~df['TicketNo'].astype(str).str.strip().isin(blacklist_tickets)]
            removed = initial_len - len(df)
            if removed > 0:
                st.info(f"⚡ {removed} Tiket otomatis disaring.")

        # D. FILTER ACTIVITY
        if 'WorkActivity' in df.columns:
            list_act = sorted(df['WorkActivity'].unique().astype(str))
            sel_act = st.multiselect("Filter Status:", list_act, default=list_act)
            df = df[df['WorkActivity'].isin(sel_act)]

        if st.button("🗑️ RESET APLIKASI"):
            st.session_state.reset_key += 1
            st.rerun()

        # E. GENERATE LAPORAN
        if not df.empty:
            df['ActualTargetDate_DT'] = pd.to_datetime(df['ActualTargetDate'])
            df = df.sort_values(['EngineerName', 'ActualTargetDate_DT', 'MerchantName'])
            
            nama_hari = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
            res_txt = ""

            for eng, g_eng in df.groupby('EngineerName'):
                h = str(eng).upper()
                st.markdown(f"<p class='engineer-header'>{h}</p>", unsafe_allow_html=True)
                res_txt += f"*{h}*\n"
                
                g_eng['Date_Only'] = g_eng['ActualTargetDate_DT'].dt.date
                for date_only, g_dt in g_eng.groupby('Date_Only'):
                    sym_tgl = "🔴" if date_only < today_date else ("🗓️" if date_only == today_date else "🟡")
                    h_indo = nama_hari.get(date_only.strftime('%A'))
                    dt_header = f"{sym_tgl} {h_indo}, {date_only.strftime('%d-%m-%Y')}"
                    
                    st.markdown(f"<p class='date-header'>{dt_header}</p>", unsafe_allow_html=True)
                    res_txt += f"{dt_header}\n"
                    
                    for _, r in g_dt.iterrows():
                        target_dt = r['ActualTargetDate_DT'].replace(tzinfo=tz_jkt)
                        selisih = (target_dt - now_jkt).total_seconds() / 3600
                        
                        if selisih <= 0:
                            color, sym_status = "#d32f2f", "❌"
                        elif selisih <= 2:
                            color, sym_status = "#fbc02d", "⚠️"
                        else:
                            color, sym_status = "#2e7d32", "✅"
                        
                        jam = r['ActualTargetDate_DT'].strftime('%H:%M')
                        display = f"• {r['MerchantName']} - {r['WorkActivity']} <span style='color:{color}; font-weight:bold;'>[{jam}]</span>"
                        wa_text = f"• {r['MerchantName']} - {r['WorkActivity']} ({jam}) {sym_status}"
                        
                        st.markdown(f"<p class='item-list'>{display}</p>", unsafe_allow_html=True)
                        res_txt += f"{wa_text}\n"
                res_txt += "\n"

            st.text_area("📋 Copy Rekap WhatsApp:", value=res_txt.strip(), height=250)

            # F. TOMBOL SHARE KE WHATSAPP
            if res_txt.strip():
                wa_encoded = quote(res_txt.strip())
                wa_url = f"https://wa.me/?text={wa_encoded}"
                
                st.markdown(f"""
                    <a href="{wa_url}" target="_blank" style="
                        display: block; text-align: center; padding: 12px;
                        background-color: #25D366; color: white !important;
                        text-decoration: none; border-radius: 8px;
                        font-size: 15px; font-weight: bold; margin-top: 10px;
                    ">📤 SHARE KE WHATSAPP</a>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
