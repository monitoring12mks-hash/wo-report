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
    
    /* Tombol Animasi */
    .mega-btn {
        display: block; width: 100%; padding: 15px; 
        background-color: #d32f2f; color: white !important; 
        border: none; border-radius: 10px; font-weight: bold;
        font-size: 16px; cursor: pointer; margin-bottom: 10px;
    }
    #status-text { font-size: 14px; color: #1565c0; font-weight: bold; text-align: center; margin-bottom: 5px; }
    .progress-container { width: 100%; background-color: #ddd; border-radius: 5px; margin-bottom: 20px; display: none; }
    .progress-bar { width: 0%; height: 10px; background-color: #2e7d32; border-radius: 5px; transition: width 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA URL
def get_report_urls():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return [
        {"n": "Scheduled", "u": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled"},
        {"n": "Booked", "u": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked"},
        {"n": "On Progress", "u": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"}
    ]

# 3. AMBIL SECRETS
try:
    GOOGLE_SHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Secrets 'GSHEET_URL' belum diisi!")
    st.stop()

st.title("📲 Monitoring WO Real-time")

# --- SEKSI 1: DOWNLOADER DENGAN ANTRIAN JAVASCRIPT ---
st.subheader("1. Download Data VCare")

urls_data = get_report_urls()

# Komponen HTML & JavaScript untuk menangani antrean download
js_component = f"""
    <div id="status-text">Siap mendownload...</div>
    <div id="p-container" class="progress-container"><div id="p-bar" class="progress-bar"></div></div>
    <button onclick="startSequence()" class="mega-btn">🚀 DOWNLOAD BERURUTAN (3 FILE)</button>

    <script>
    async function startSequence() {{
        const reports = {urls_data};
        const btn = document.querySelector('.mega-btn');
        const status = document.getElementById('status-text');
        const container = document.getElementById('p-container');
        const bar = document.getElementById('p-bar');

        btn.disabled = true;
        btn.style.backgroundColor = '#999';
        container.style.display = 'block';

        for (let i = 0; i < reports.length; i++) {{
            status.innerText = "Mendownload: " + reports[i].n + "...";
            bar.style.width = ((i + 1) / reports.length * 100) + "%";
            
            // Trigger download
            const link = document.createElement('a');
            link.href = reports[i].u;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Menunggu 2 detik sebelum file berikutnya untuk memastikan browser memproses
            await new Promise(resolve => setTimeout(resolve, 2000));
        }}

        status.innerText = "✅ Selesai! Silakan cek folder Download.";
        btn.disabled = false;
        btn.style.backgroundColor = '#d32f2f';
    }}
    </script>
"""
st.markdown(js_component, unsafe_allow_html=True)
st.caption("💡 Jika hanya 1 file yang terdownload, klik ikon 'Pop-up Blocked' di address bar lalu pilih **Always Allow**.")

st.markdown("---")

# --- SEKSI 2: PENGOLAHAN DATA ---
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
uploaded_files = st.file_uploader("2. Upload file hasil download:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    try:
        dfs = []
        for f in uploaded_files:
            temp = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
            temp.columns = [c.strip() for c in temp.columns]
            dfs.append(temp)
        
        df = pd.concat(dfs, ignore_index=True)

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
    except:
        st.error("Gagal memproses file.")
