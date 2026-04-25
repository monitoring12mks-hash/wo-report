import streamlit as st
import pandas as pd
import datetime
import pytz
from urllib.parse import quote

# 1. KONFIGURASI HALAMAN & CSS
st.set_page_config(page_title="WO Reporter SLA Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="manage-app-button"] {display: none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    [data-testid="stFileUploadDropzone"] { border: 2px dashed #1565c0; background-color: #f0f7ff; }
    p, span, label, div { color: black !important; }

    .btn-download { 
        display: block; text-align: center; padding: 12px; background-color: #2e7d32; color: white !important; 
        text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin-bottom: 10px;
    }
    .btn-download:hover { background-color: #1b5e20; opacity: 0.9; }

    .engineer-header {
        font-weight: bold; color: black; margin-top: 15px;
        text-decoration: underline; font-size: 16px;
    }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }

    .info-box {
        background-color: #e3f2fd; border-left: 5px solid #1565c0;
        padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 14px;
    }

    /* ── SUMMARY TABLE ── */
    .summary-box {
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 20px;
    }
    .summary-title {
        font-size: 15px; font-weight: bold; color: #1565c0 !important;
        margin-bottom: 10px;
    }
    .summary-table {
        width: 100%; border-collapse: collapse; font-size: 13px;
    }
    .summary-table th {
        background-color: #1565c0; color: white !important;
        padding: 6px 10px; text-align: left;
    }
    .summary-table td {
        padding: 5px 10px; border-bottom: 1px solid #eee;
    }
    .summary-table tr:last-child td { border-bottom: none; }
    .summary-table tr:hover td { background-color: #e8f0fe; }

    /* badge warna */
    .badge {
        display: inline-block; border-radius: 12px;
        padding: 2px 9px; font-size: 12px; font-weight: bold; color: white !important;
    }
    .badge-red   { background-color: #d32f2f; }
    .badge-yellow{ background-color: #f9a825; }
    .badge-green { background-color: #2e7d32; }
    .badge-blue  { background-color: #1565c0; }

    /* engineer header row */
    .eng-header-row {
        display: flex; align-items: center; gap: 10px;
        margin-top: 18px; margin-bottom: 2px;
    }
    .eng-name {
        font-weight: bold; font-size: 16px;
        text-decoration: underline; color: black !important;
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

# --- FUNGSI DOWNLOADER ---
def get_links(d_from, d_to):
    f_from = d_from.strftime("%d-%b-%Y")
    f_to   = d_to.strftime("%d-%b-%Y")
    enc    = lambda s: quote(s)
    base   = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    return {
        "Assigning":   f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Assigning",
        "Scheduled":   f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Scheduled",
        "Booked":      f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Booked",
        "On Progress": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=On%20Progress",
    }

# --- HELPER: hitung status tiket ---
def ticket_status(target_dt_aware, now_aware):
    selisih = (target_dt_aware - now_aware).total_seconds() / 3600
    if selisih <= 0:
        return "overdue"
    elif selisih <= 2:
        return "warning"
    else:
        return "aman"

# ==================================================
# UI UTAMA
# ==================================================
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
    st.markdown(
        '<div class="info-box"><b>💻 MODE PC AKTIF</b><br>'
        'Klik tombol satu per satu dan tentukan folder penyimpanan Anda.</div>',
        unsafe_allow_html=True
    )

for name, url in links.items():
    st.markdown(
        f'<a href="{url}" target="_blank" class="btn-download">📥 DOWNLOAD {name.upper()}</a>',
        unsafe_allow_html=True
    )

st.markdown("---")

# ==================================================
# SEKSI UPLOAD & PROSES
# ==================================================
st.subheader("Langkah 2: Upload & Rekap")

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

uploaded_files = st.file_uploader(
    "Upload file Excel/CSV:", type=['xlsx', 'csv'],
    accept_multiple_files=True, key=f"up_{st.session_state.reset_key}"
)

if uploaded_files:
    try:
        # A. LOAD BLACKLIST
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
            sel_act  = st.multiselect("Filter Status:", list_act, default=list_act)
            df       = df[df['WorkActivity'].isin(sel_act)]

        if st.button("🗑️ RESET APLIKASI"):
            st.session_state.reset_key += 1
            st.rerun()

        # E. GENERATE LAPORAN
        if not df.empty:
            df['ActualTargetDate_DT'] = pd.to_datetime(df['ActualTargetDate'])
            df = df.sort_values(['EngineerName', 'ActualTargetDate_DT', 'MerchantName'])

            # ── HITUNG STATUS PER TIKET ──────────────────────────────────────
            def classify(row):
                target_dt = row['ActualTargetDate_DT'].replace(tzinfo=tz_jkt)
                return ticket_status(target_dt, now_jkt)

            df['_status'] = df.apply(classify, axis=1)

            # ── SUMMARY TABLE PER ENGINEER ───────────────────────────────────
            summary = (
                df.groupby(['EngineerName', '_status'])
                  .size()
                  .unstack(fill_value=0)
                  .reindex(columns=['overdue', 'warning', 'aman'], fill_value=0)
                  .reset_index()
            )
            summary['Total'] = summary['overdue'] + summary['warning'] + summary['aman']
            summary = summary.sort_values('Total', ascending=False)

            # Render tabel ringkasan
            total_all = summary['Total'].sum()
            rows_html  = ""
            for _, row in summary.iterrows():
                od = f"<span class='badge badge-red'>{row['overdue']}</span>"   if row['overdue']  else "<span style='color:#aaa'>0</span>"
                wa = f"<span class='badge badge-yellow'>{row['warning']}</span>" if row['warning']  else "<span style='color:#aaa'>0</span>"
                ok = f"<span class='badge badge-green'>{row['aman']}</span>"     if row['aman']     else "<span style='color:#aaa'>0</span>"
                tot= f"<span class='badge badge-blue'>{row['Total']}</span>"
                rows_html += f"<tr><td>{row['EngineerName']}</td><td>{od}</td><td>{wa}</td><td>{ok}</td><td>{tot}</td></tr>"

            st.markdown(f"""
            <div class="summary-box">
                <div class="summary-title">📊 Ringkasan Tiket Aktif — Total: {total_all} tiket</div>
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Engineer</th>
                            <th>❌ Overdue</th>
                            <th>⚠️ &lt; 2 Jam</th>
                            <th>✅ Aman</th>
                            <th>🎫 Total</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # ── DETAIL PER ENGINEER ──────────────────────────────────────────
            nama_hari = {
                "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
                "Thursday": "Kamis", "Friday": "Jumat",
                "Saturday": "Sabtu", "Sunday": "Minggu"
            }
            res_txt = ""

            for eng, g_eng in df.groupby('EngineerName'):
                eng_str   = str(eng).upper()
                total_eng = len(g_eng)

                # hitung breakdown per engineer untuk badge header
                od_cnt = (g_eng['_status'] == 'overdue').sum()
                wa_cnt = (g_eng['_status'] == 'warning').sum()
                ok_cnt = (g_eng['_status'] == 'aman').sum()

                badge_parts = []
                if od_cnt: badge_parts.append(f"<span class='badge badge-red'>❌ {od_cnt}</span>")
                if wa_cnt: badge_parts.append(f"<span class='badge badge-yellow'>⚠️ {wa_cnt}</span>")
                if ok_cnt: badge_parts.append(f"<span class='badge badge-green'>✅ {ok_cnt}</span>")
                badge_parts.append(f"<span class='badge badge-blue'>🎫 {total_eng}</span>")

                badges_html = " ".join(badge_parts)

                st.markdown(
                    f"<div class='eng-header-row'>"
                    f"  <span class='eng-name'>{eng_str}</span>"
                    f"  {badges_html}"
                    f"</div>",
                    unsafe_allow_html=True
                )
                res_txt += f"*{eng_str}* ({total_eng} tiket)\n"

                g_eng = g_eng.copy()
                g_eng['Date_Only'] = g_eng['ActualTargetDate_DT'].dt.date
                for date_only, g_dt in g_eng.groupby('Date_Only'):
                    sym_tgl = "🔴" if date_only < today_date else ("🗓️" if date_only == today_date else "🟡")
                    h_indo  = nama_hari.get(date_only.strftime('%A'))
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
                        display = (
                            f"• {r['MerchantName']} - {r['WorkActivity']} "
                            f"<span style='color:{color}; font-weight:bold;'>[{jam}]</span>"
                        )
                        wa_text = f"• {r['MerchantName']} - {r['WorkActivity']} ({jam}) {sym_status}"

                        st.markdown(f"<p class='item-list'>{display}</p>", unsafe_allow_html=True)
                        res_txt += f"{wa_text}\n"
                res_txt += "\n"

            # ── TEXT AREA WHATSAPP ───────────────────────────────────────────
            st.text_area("📋 Copy Rekap WhatsApp:", value=res_txt.strip(), height=250)

            if res_txt.strip():
                wa_encoded = quote(res_txt.strip())
                wa_url     = f"https://wa.me/?text={wa_encoded}"
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
