import streamlit as st
import pandas as pd

st.title("Mencari Nama Kolom Asli")

try:
    # Membaca sheet 'INFO' dari file data.xlsx
    df_info = pd.read_excel("data.xlsx", sheet_name="INFO")
    
    st.header("Berhasil Membaca File!")
    
    # Menampilkan daftar nama kolom asli
    st.subheader("Nama-nama Kolom di Sheet 'INFO':")
    st.write(df_info.columns.tolist())
    
    # Menampilkan 5 baris pertama dari data untuk referensi
    st.subheader("Contoh 5 Baris Pertama Data:")
    st.dataframe(df_info.head())

except FileNotFoundError:
    st.error("File 'data.xlsx' tidak ditemukan di repository. Mohon periksa kembali.")
except Exception as e:
    st.error(f"Terjadi error saat membaca file Excel: {e}")
