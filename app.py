import streamlit as st
import pandas as pd
import datetime
import pytz
from urllib.parse import quote

# 1. KONFIGURASI HALAMAN & CSS
st.set_page_config(page_title="WO Reporter SLA Pro", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600;700&display=swap');

    .stApp { background-color: #f5f6fa; color: black; font-family: 'IBM Plex Sans', sans-serif; }
    header, footer { visibility: hidden; }
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #1565c0; background-color: #f0f7ff; }
    p, span, label, div { color: black !important; }

    /* --- SUMMARY PANEL --- */
    .summary-panel {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border-top: 5px solid #1565c0;
    }
    .summary-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 2px;
        color: #1565c0 !important;
        text-transform: uppercase;
        margin-bottom: 16px;
    }
    .summary-cards {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }
    .sla-card {
        flex: 1;
        min-width: 120px;
        border-radius: 10px;
        padding: 14px 16px;
        text-align: center;
    }
    .sla-card.total  { background: #e8eaf6; border: 2px solid #3949ab; }
    .sla-card.danger { background: #ffebee; border: 2px solid #c62828; }
    .sla-card.warn   { background: #fff8e1; border: 2px solid #f9a825; }
    .sla-card.safe   { background: #e8f5e9; border: 2px solid #2e7d32; }

    .sla-card .num {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 4px;
    }
    .sla-card.total  .num { color: #3949ab !important; }
    .sla-card.danger .num { color: #c62828 !important; }
    .sla-card.warn   .num { color: #f9a825 !important; }
    .sla-card.safe   .num { color: #2e7d32 !important; }

    .sla-card .lbl {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .sla-card.total  .lbl { color: #3949ab !important; }
    .sla-card.danger .lbl { color: #c62828 !important; }
    .sla-card.warn   .lbl { color: #f9a825 !important; }
    .sla-card.safe   .lbl { color: #2e7d32 !important; }

    .sla-card .icon  { font-size: 20px; margin-bottom: 6px; }

    /* --- PROGRESS BAR SLA --- */
    .sla-bar-wrap {
        margin-top: 18px;
    }
    .sla-bar-label {
        font-size: 12px;
        color: #555 !important;
        margin-bottom: 5px;
        font-weight: 600;
    }
    .sla-bar-track {
        height: 14px;
        border-radius: 7px;
        background: #e0e0e0;
        display: flex;
        overflow: hidden;
    }
    .sla-seg-danger { background: #c62828; }
    .sla-seg-warn   { background: #f9a825; }
    .sla-seg-safe   { background: #2e7d32; }

    /* --- KRITIS LIST --- */
    .kritis-section {
        background: #fff3e0;
        border-left: 5px solid #e65100;
        border-radius: 0 10px 10px 0;
        padding: 14px 18px;
        margin-top: 16px;
    }
    .kritis-title {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #e65100 !important;
        margin-bottom: 10px;
    }
    .kritis-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        border-radius: 7px;
        padding: 8px 12px;
        margin-bottom: 6px;
        border-left: 4px solid #c62828;
        font-size: 13px;
    }
    .kritis-item .ki-merchant { font-weight: 600; color: #222 !important; }
    .kritis-item .ki-eng     { color: #666 !important; font-size: 11px; }
    .kritis-item .ki-time    { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 700; color: #c62828 !important; }

    .warn-item {
        border-left-color: #f9a825;
    }
    .warn-item .ki-time { color: #f57f17 !important; }

    /* --- TOMBOL & LAINNYA --- */
    .btn-download {
        display: block; text-align: center; padding: 12px;
        background-color: #2e7d32; color: white !important;
        text-decoration: none; border-radius: 8px;
        font-size: 14px; font-weight: bold; margin-bottom: 10px;
    }
    .btn-download:hover { background-color: #1b5e20; }

    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }

    .info-box {
        background-color: #e3f2fd; border-left: 5px solid #1565c0;
        padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. ZONA WAKTU
tz_jkt = pytz.timezone('Asia/Jakarta')
now_jkt = datetime.datetime.now(tz_jkt)
today_date = now_jkt.date()

# 3. SECRETS
try:
    GOOGLE_SHEET_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Secrets 'GSHEET_URL' tidak ditemukan di Streamlit Cloud!")
    st.stop()

# --- DOWNLOADER ---
def get_links(d_from, d_to):
    f_from = d_from.strftime("%d-%b-%Y")
    f_to   = d_to.strftime("%d-%b-%Y")
    enc    = lambda s: quote(s)
    base   = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return {
        "Scheduled":   f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Scheduled",
        "Booked":      f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Booked",
        "On Progress": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=On%20Progress"
    }

# --- FUNGSI SUMMARY HTML ---
def render_summary(df_active, now_jkt):
    """Tampilkan panel ringkasan SLA di atas laporan."""
    rows = []
    for _, r in df_active.iterrows():
        target_dt = r['ActualTargetDate_DT'].replace(tzinfo=tz_jkt)
        selisih   = (target_dt - now_jkt).total_seconds() / 3600
        rows.append({
            'MerchantName': r.get('MerchantName', '-'),
            'EngineerName': r.get('EngineerName', '-'),
            'WorkActivity': r.get('WorkActivity', '-'),
            'jam':          r['ActualTargetDate_DT'].strftime('%H:%M'),
            'tanggal':      r['ActualTargetDate_DT'].strftime('%d-%m-%Y'),
            'selisih':      selisih,
        })

    total   = len(rows)
    danger  = sum(1 for x in rows if x['selisih'] <= 0)
    warn    = sum(1 for x in rows if 0 < x['selisih'] <= 2)
    safe    = sum(1 for x in rows if x['selisih'] > 2)

    # Hitung lebar bar
    def pct(n):
        return round(n / total * 100, 1) if total else 0

    bar_html = ""
    if total > 0:
        segs = []
        if danger: segs.append(f'<div class="sla-seg-danger" style="width:{pct(danger)}%"></div>')
        if warn:   segs.append(f'<div class="sla-seg-warn"   style="width:{pct(warn)}%"></div>')
        if safe:   segs.append(f'<div class="sla-seg-safe"   style="width:{pct(safe)}%"></div>')
        bar_html = f"""
        <div class="sla-bar-wrap">
            <div class="sla-bar-label">Distribusi SLA ({total} WO Aktif)</div>
            <div class="sla-bar-track">{''.join(segs)}</div>
        </div>
        """

    # Daftar kritis & warning (sortir paling mepet dulu)
    kritis_items = sorted([x for x in rows if x['selisih'] <= 2], key=lambda x: x['selisih'])
    kritis_html  = ""
    if kritis_items:
        items_html = ""
        for x in kritis_items:
            is_over = x['selisih'] <= 0
            cls     = "kritis-item" if is_over else "kritis-item warn-item"
            icon    = "❌" if is_over else "⚠️"
            jam_lbl = f"LEWAT" if is_over else f"≈{x['selisih']:.1f}j"
            tgl_lbl = x['tanggal'] if is_over else x['jam']
            items_html += f"""
            <div class="{cls}">
                <div>
                    <div class="ki-merchant">{icon} {x['MerchantName']}</div>
                    <div class="ki-eng">{x['EngineerName']} · {x['WorkActivity']} · {x['jam']} {x['tanggal']}</div>
                </div>
                <div class="ki-time">{jam_lbl}</div>
            </div>"""
        kritis_html = f"""
        <div class="kritis-section">
            <div class="kritis-title">⚡ Perlu Perhatian Segera</div>
            {items_html}
        </div>"""

    html = f"""
    <div class="summary-panel">
        <div class="summary-title">📊 Ringkasan SLA — Per {now_jkt.strftime('%d %b %Y %H:%M')} WIB</div>
        <div class="summary-cards">
            <div class="sla-card total">
                <div class="icon">📋</div>
                <div class="num">{total}</div>
                <div class="lbl">Total WO</div>
            </div>
            <div class="sla-card danger">
                <div class="icon">❌</div>
                <div class="num">{danger}</div>
                <div class="lbl">SLA Lewat</div>
            </div>
            <div class="sla-card warn">
                <div class="icon">⚠️</div>
                <div class="num">{warn}</div>
                <div class="lbl">Kritis ≤2j</div>
            </div>
            <div class="sla-card safe">
                <div class="icon">✅</div>
                <div class="num">{safe}</div>
                <div class="lbl">Aman &gt;2j</div>
            </div>
        </div>
        {bar_html}
        {kritis_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ===================== UI UTAMA =====================
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

# ===================== UPLOAD & PROSES =====================
st.subheader("Langkah 2: Upload & Rekap")

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader(
    "Upload file Excel/CSV:",
    type=['xlsx', 'csv'],
    accept_multiple_files=True,
    key=f"up_{st.session_state.reset_key}"
)

if uploaded_files:
    try:
        # A. BLACKLIST
        @st.cache_data(ttl=300)
        def get_blacklist():
            try:
                sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
                csv_url  = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                db       = pd.read_csv(csv_url)
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
            sel_act  = st.multiselect("Filter Status:", list_act, default=list_act)
            df       = df[df['WorkActivity'].isin(sel_act)]

        if st.button("🗑️ RESET APLIKASI"):
            st.session_state.reset_key += 1
            st.rerun()

        # E. PROSES & TAMPILKAN
        if not df.empty:
            df['ActualTargetDate_DT'] = pd.to_datetime(df['ActualTargetDate'])
            df = df.sort_values(['EngineerName', 'ActualTargetDate_DT', 'MerchantName'])

            # ── SUMMARY PANEL ──────────────────────────────
            render_summary(df, now_jkt)
            # ──────────────────────────────────────────────

            nama_hari = {
                "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
                "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
            }
            res_txt = ""

            for eng, g_eng in df.groupby('EngineerName'):
                h = str(eng).upper()
                st.markdown(f"<p class='engineer-header'>{h}</p>", unsafe_allow_html=True)
                res_txt += f"*{h}*\n"

                g_eng = g_eng.copy()
                g_eng['Date_Only'] = g_eng['ActualTargetDate_DT'].dt.date

                for date_only, g_dt in g_eng.groupby('Date_Only'):
                    sym_tgl  = "🔴" if date_only < today_date else ("🗓️" if date_only == today_date else "🟡")
                    h_indo   = nama_hari.get(date_only.strftime('%A'))
                    dt_header = f"{sym_tgl} {h_indo}, {date_only.strftime('%d-%m-%Y')}"

                    st.markdown(f"<p class='date-header'>{dt_header}</p>", unsafe_allow_html=True)
                    res_txt += f"{dt_header}\n"

                    for _, r in g_dt.iterrows():
                        target_dt = r['ActualTargetDate_DT'].replace(tzinfo=tz_jkt)
                        selisih   = (target_dt - now_jkt).total_seconds() / 3600

                        if selisih <= 0:
                            color, sym_status = "#d32f2f", "❌"
                        elif selisih <= 2:
                            color, sym_status = "#fbc02d", "⚠️"
                        else:
                            color, sym_status = "#2e7d32", "✅"

                        jam     = r['ActualTargetDate_DT'].strftime('%H:%M')
                        display = f"• {r['MerchantName']} - {r['WorkActivity']} <span style='color:{color}; font-weight:bold;'>[{jam}]</span>"
                        wa_text = f"• {r['MerchantName']} - {r['WorkActivity']} ({jam}) {sym_status}"

                        st.markdown(f"<p class='item-list'>{display}</p>", unsafe_allow_html=True)
                        res_txt += f"{wa_text}\n"
                res_txt += "\n"

            st.text_area("📋 Copy Rekap WhatsApp:", value=res_txt, height=250)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
