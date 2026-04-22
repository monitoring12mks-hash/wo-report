import streamlit as st
import pandas as pd
import datetime
import pytz
from urllib.parse import quote

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="WO Reporter SLA Pro", layout="centered")

# CSS
st.markdown("""
<style>
.stApp { background-color: white; color: black; }
header, footer, #MainMenu {visibility: hidden;}
.stDeployButton {display:none;}
[data-testid="manage-app-button"] {display: none;}
[data-testid="stStatusWidget"] {visibility: hidden;}
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed #1565c0;
    background-color: #f0f7ff;
}
.btn-download {
    display: block; text-align: center; padding: 12px;
    background-color: #2e7d32; color: white !important;
    text-decoration: none; border-radius: 8px;
    font-weight: bold; margin-bottom: 10px;
}
.engineer-header { font-weight: bold; margin-top: 15px; text-decoration: underline; }
.date-header { font-weight: bold; margin-left: 10px; }
.item-list { margin-left: 25px; }
</style>
""", unsafe_allow_html=True)

# ===============================
# TIMEZONE
# ===============================
tz_jkt = pytz.timezone('Asia/Jakarta')
now_jkt = datetime.datetime.now(tz_jkt)
today_date = now_jkt.date()

# ===============================
# SECRETS
# ===============================
try:
    GOOGLE_SHEET_URL = st.secrets["GSHEET_URL"]
except Exception:
    st.error("⚠️ GSHEET_URL tidak ditemukan!")
    st.stop()

# ===============================
# FUNCTIONS
# ===============================
def get_links(d_from, d_to):
    f_from = d_from.strftime("%d-%b-%Y")
    f_to = d_to.strftime("%d-%b-%Y")
    base = "https://vcare.visionet.co.id/Report/DownloadReportByStatus"
    enc = lambda x: quote(x)

    return {
        "Assigning": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Assigning",
        "Scheduled": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Scheduled",
        "Booked": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=Booked",
        "On Progress": f"{base}?DateFrom={enc(f_from)}&DateTo={enc(f_to)}&WorkActivity=On%20Progress",
    }

@st.cache_data(ttl=300)
def get_blacklist():
    try:
        sheet_id = GOOGLE_SHEET_URL.split("/d/")[1].split("/")[0]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        return df['TicketNo'].astype(str).str.strip().unique().tolist()
    except Exception:
        return []

# ===============================
# UI
# ===============================
st.title("📲 WO Monitoring & SLA")

mode = st.radio("Mode:", ["📱 Mobile", "💻 PC"], horizontal=True)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Dari", today_date.replace(day=1))
with col2:
    end_date = st.date_input("Sampai", today_date)

links = get_links(start_date, end_date)

st.subheader("Download Data")
for name, url in links.items():
    st.markdown(f'<a href="{url}" target="_blank" class="btn-download">📥 {name}</a>', unsafe_allow_html=True)

st.markdown("---")

# ===============================
# UPLOAD
# ===============================
if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0

files = st.file_uploader(
    "Upload Excel/CSV",
    type=["xlsx", "csv"],
    accept_multiple_files=True,
    key=f"up_{st.session_state.reset_key}"
)

# ===============================
# PROCESS
# ===============================
if files:
    try:
        blacklist = get_blacklist()

        dfs = []
        for f in files:
            if f.name.endswith(".csv"):
                df_temp = pd.read_csv(f)
            else:
                df_temp = pd.read_excel(f)

            df_temp.columns = [c.strip() for c in df_temp.columns]
            dfs.append(df_temp)

        df = pd.concat(dfs, ignore_index=True)

        # VALIDASI KOLOM
        required = ['EngineerName', 'ActualTargetDate', 'MerchantName', 'WorkActivity']
        for col in required:
            if col not in df.columns:
                st.error(f"Kolom {col} tidak ditemukan!")
                st.stop()

        # CLEANING
        df['EngineerName'] = df['EngineerName'].fillna("BELUM DI-ASSIGN")
        df['ActualTargetDate'] = df['ActualTargetDate'].fillna(now_jkt)

        # FILTER BLACKLIST
        if 'TicketNo' in df.columns:
            df = df[~df['TicketNo'].astype(str).isin(blacklist)]

        # FILTER ACTIVITY
        act_list = sorted(df['WorkActivity'].astype(str).unique())
        selected = st.multiselect("Filter Status", act_list, default=act_list)
        df = df[df['WorkActivity'].isin(selected)]

        if st.button("RESET"):
            st.session_state.reset_key += 1
            st.rerun()

        # ===============================
        # GENERATE REPORT
        # ===============================
        if not df.empty:
            df['ActualTargetDate'] = pd.to_datetime(df['ActualTargetDate'])
            df = df.sort_values(['EngineerName', 'ActualTargetDate'])

            hari_map = {
                "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
                "Thursday": "Kamis", "Friday": "Jumat",
                "Saturday": "Sabtu", "Sunday": "Minggu"
            }

            result = ""

            for eng, g in df.groupby('EngineerName'):
                g = g.copy()
                g['DateOnly'] = g['ActualTargetDate'].dt.date

                st.markdown(f"**{eng.upper()}**")
                result += f"*{eng.upper()}*\n"

                for d, g2 in g.groupby('DateOnly'):
                    hari = hari_map[d.strftime("%A")]
                    header = f"{hari}, {d.strftime('%d-%m-%Y')}"

                    st.markdown(f"- {header}")
                    result += f"{header}\n"

                    for _, r in g2.iterrows():
                        jam = r['ActualTargetDate'].strftime("%H:%M")
                        line = f"• {r['MerchantName']} - {r['WorkActivity']} ({jam})"

                        st.write(line)
                        result += line + "\n"

                result += "\n"

            st.text_area("Copy WA", result.strip(), height=250)

            if result.strip():
                wa = quote(result.strip())
                st.markdown(
                    f'<a href="https://wa.me/?text={wa}" target="_blank">📤 Share WA</a>',
                    unsafe_allow_html=True
                )

    except Exception as e:
        st.error(f"Error: {e}")
