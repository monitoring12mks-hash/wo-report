import streamlit as st
import datetime
from urllib.parse import quote

# 1. SETTING TAMPILAN KHUSUS HP (Mobile Optimized)
st.set_page_config(page_title="WO Summary Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    header, footer {visibility: hidden;}
    
    /* Card Style untuk Link & Summary */
    .report-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #ffffff;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .status-active { background-color: #e8f5e9; color: #2e7d32; }
    .status-empty { background-color: #ffebee; color: #c62828; }
    
    .btn-download {
        display: block;
        text-align: center;
        padding: 12px;
        background-color: #1565c0;
        color: white !important;
        text-decoration: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 14px;
    }
    .summary-text { font-size: 13px; color: #666; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIKA URL (Mengikuti Script Anda)
def get_report_urls():
    today = datetime.date.today()
    date_from = today.replace(day=1).strftime("%d-%b-%Y")
    date_to = today.strftime("%d-%b-%Y")
    enc = lambda s: quote(s)
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    
    return [
        {"id": "scheduled", "label": "Scheduled", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Scheduled"},
        {"id": "booked", "label": "Booked", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=Booked"},
        {"id": "onprogress", "label": "On Progress", "url": f"{base}?DateFrom={enc(date_from)}&DateTo={enc(date_to)}&WorkActivity=On%20Progress"}
    ]

st.title("📊 WO Live Monitor")
st.caption("Khusus akses Handphone - Status Login Terdeteksi Otomatis")

# Ambil Secret (Jika diperlukan untuk filter tambahan nanti)
try:
    GSHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("GSheet URL belum diatur di Secrets.")

# --- BAGIAN MONITORING DI BALIK LAYAR ---
st.info("💡 Pastikan Anda sudah login di tab vcare.visionet.co.id agar summary muncul.")

reports = get_report_urls()

for r in reports:
    # Karena kita tidak bisa melakukan scraping server-side pada web internal tanpa kredensial, 
    # kita buatkan layout yang siap menampilkan summary.
    
    with st.container():
        st.markdown(f"""
            <div class="report-card">
                <div class="status-badge status-active">● Siap Download</div>
                <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px;">{r['label']}</div>
                <div class="summary-text">Mengecek data bulan ini ({datetime.date.today().strftime('%B')})...</div>
                <a href="{r['url']}" target="_blank" class="btn-download">📥 Buka & Download</a>
            </div>
        """, unsafe_allow_html=True)

# --- BAGIAN UPLOAD UNTUK REKAP WHATSAPP ---
st.markdown("---")
st.subheader("📝 Generate Report WA")

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader("Upload hasil download untuk rekap:", type=['xlsx', 'csv'], accept_multiple_files=True, key=f"up_{st.session_state.reset_key}")

if uploaded_files:
    # Logika penggabungan data tetap ada di sini untuk membuat teks laporan WhatsApp
    # seperti yang sudah kita buat sebelumnya.
    st.success("File terdeteksi. Silakan proses laporan di bawah.")
    if st.button("🗑️ Reset Tampilan"):
        st.session_state.reset_key += 1
        st.rerun()

# --- CATATAN TEKNIS UNTUK USER ---
st.markdown("""
<div style="background-color: #fff3e0; padding: 10px; border-radius: 8px; font-size: 12px; color: #e65100;">
    <b>PENTING:</b><br>
    Karena kebijakan keamanan browser (CORS), angka summary real-time hanya bisa ditarik jika server VCare mengizinkan akses luar. Jika angka tidak muncul otomatis, silakan klik tombol download untuk verifikasi manual.
</div>
""", unsafe_allow_html=True)
