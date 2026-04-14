import streamlit as st
import pandas as pd

# Tampilan bersih
st.set_page_config(page_title="WO Reporter Pivot", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    p { margin-bottom: 2px; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    .engineer-header { font-weight: bold; color: #000; margin-top: 15px; text-decoration: underline; }
    .date-header { font-weight: bold; color: #444; margin-left: 10px; margin-top: 5px; }
    .item-list { margin-left: 25px; color: #333; }
    </style>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Bersihkan nama kolom
        df.columns = [c.strip() for c in df.columns]

        # Pastikan kolom Tanggal terbaca sebagai tanggal yang rapi (YYYY-MM-DD)
        date_col = 'ActualTargetDate'
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')

        # Mengikuti struktur Pivot: Engineer -> Date -> Merchant -> Activity
        # Kita urutkan agar rapi
        df = df.sort_values(['EngineerName', 'ActualTargetDate', 'MerchantName'])

        # Grouping Data
        for eng, eng_group in df.groupby('EngineerName'):
            # BAGIAN ROWS 1: EngineerName
            st.markdown(f"<p class='engineer-header'>{str(eng).upper()}</p>", unsafe_allow_html=True)
            
            for dt, dt_group in eng_group.groupby('ActualTargetDate'):
                # BAGIAN ROWS 2: ActualTargetDate
                st.markdown(f"<p class='date-header'>📅 {dt}</p>", unsafe_allow_html=True)
                
                for _, row in dt_group.iterrows():
                    # BAGIAN ROWS 3 & 4: MerchantName & WorkActivity
                    merchant = row['MerchantName']
                    activity = row['WorkActivity']
                    st.markdown(f"<p class='item-list'>• {merchant} - {activity}</p>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}. Pastikan nama kolom di Excel sesuai (EngineerName, ActualTargetDate, MerchantName, WorkActivity).")
