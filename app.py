import streamlit as st
import pandas as pd

# 1. SETTING CSS: Memaksa latar belakang putih & teks hitam (Mencegah masalah Dark Mode)
st.set_page_config(page_title="WO Reporter", layout="centered")

st.markdown("""
    <style>
    /* Memaksa background putih di seluruh aplikasi */
    .stApp { background-color: white; color: black; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Styling teks agar tetap hitam meski HP user Dark Mode */
    p, span, label, div { color: black !important; }
    
    .engineer-header { font-weight: bold; color: black; margin-top: 15px; text-decoration: underline; font-size: 16px; }
    .date-header { font-weight: bold; color: #333; margin-left: 10px; margin-top: 5px; font-size: 14px; }
    .item-list { margin-left: 25px; color: #444; font-size: 14px; margin-bottom: 2px; }
    
    /* Style untuk tombol reset agar kontras */
    .stButton>button { background-color: #f0f0f0; color: black; border: 1px solid #ccc; }
    </style>
    """, unsafe_allow_html=True)

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.title("📲 Report Kerja Engineer")

uploaded_file = st.file_uploader("Upload file Excel / CSV", type=['xlsx', 'csv'], key="uploader")

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        df.columns = [c.strip() for c in df.columns]

        # Filter WorkActivity
        if 'WorkActivity' in df.columns:
            all_activities = sorted(df['WorkActivity'].unique().astype(str))
            selected_activities = st.multiselect("Filter WorkActivity:", options=all_activities, default=all_activities)
            df = df[df['WorkActivity'].isin(selected_activities)]

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Mulai Dari Awal"):
                reset_app()

        st.markdown("---")

        if not df.empty:
            date_col = 'ActualTargetDate'
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')

            df = df.sort_values(['EngineerName', 'ActualTargetDate', 'MerchantName'])

            # Menyiapkan variabel untuk fitur "Copy to Clipboard"
            full_text_report = ""

            # Loop untuk tampilan di layar
            for eng, eng_group in df.groupby('EngineerName'):
                header = f"{str(eng).upper()}"
                st.markdown(f"<p class='engineer-header'>{header}</p>", unsafe_allow_html=True)
                full_text_report += f"*{header}*\n"
                
                for dt, dt_group in eng_group.groupby('ActualTargetDate'):
                    date_line = f"📅 {dt}"
                    st.markdown(f"<p class='date-header'>{date_line}</p>", unsafe_allow_html=True)
                    full_text_report += f"{date_line}\n"
                    
                    for _, row in dt_group.iterrows():
                        item = f"• {row['MerchantName']} - {row['WorkActivity']}"
                        st.markdown(f"<p class='item-list'>{item}</p>", unsafe_allow_html=True)
                        full_text_report += f"{item}\n"
                full_text_report += "\n"

            st.markdown("---")
            
            # SOLUSI DATA BANYAK: Tombol Salin Teks
            st.subheader("📋 Copy Hasil")
            st.text_area("Klik kotak di bawah, pilih semua (Ctrl+A / Long Press), lalu Copy untuk Paste ke WA:", value=full_text_report, height=200)
            st.info("Gunakan kotak teks di atas jika data terlalu panjang untuk di-screenshot agar hasil di WhatsApp tidak pecah.")
            
    except Exception as e:
        st.error(f"Error: {e}")
