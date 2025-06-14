import streamlit as st
import pandas as pd

st.title("Mencari Nama Kolom di Sheet PARAMETER")

try:
    # Membaca sheet 'PARAMETER' dari file data.xlsx
    df_param = pd.read_excel("data.xlsx", sheet_name="PARAMETER")
    
    st.header("Nama Kolom Asli di Sheet 'PARAMETER':")
    
    # Menampilkan daftar nama kolom asli
    st.write(df_param.columns.tolist())
    
    # Menampilkan 5 baris pertama dari data untuk referensi
    st.subheader("Contoh 5 Baris Pertama Data:")
    st.dataframe(df_param.head())

except Exception as e:
    st.error(f"Terjadi error saat membaca file Excel: {e}")
