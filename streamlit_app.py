import streamlit as st
import pandas as pd

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    layout="wide",
    page_title="DEBUGGING...",
    page_icon="🐛"
)

st.title("🐛 Mode Debugging")
st.write("Memulai eksekusi skrip...")

try:
    st.write("Mencoba memuat data dari Excel...")
    
    # Menggunakan fungsi loader yang sama persis
    @st.cache_data
    def load_data_from_excel(path="data.xlsx"):
        def read_and_clean_sheet(xls_file, sheet_name):
            df = pd.read_excel(xls_file, sheet_name)
            df.columns = df.columns.str.strip().str.lower()
            return df
        xls = pd.ExcelFile(path)
        df_info_raw = pd.read_excel(xls, sheet_name="INFO")
        df_info_raw.columns = df_info_raw.columns.str.strip().str.lower()
        df_prov = df_info_raw[['klaster', 'provinsi']].copy(); df_prov.rename(columns={'provinsi': 'pemda'}, inplace=True); df_prov['tingkat'] = 'provinsi'
        df_kota = df_info_raw[['klaster.1', 'kota']].copy(); df_kota.rename(columns={'klaster.1': 'klaster', 'kota': 'pemda'}, inplace=True); df_kota['tingkat'] = 'kota'
        df_kab = df_info_raw[['klaster.2', 'kabupaten']].copy(); df_kab.rename(columns={'klaster.2': 'klaster', 'kabupaten': 'pemda'}, inplace=True); df_kab['tingkat'] = 'kabupaten'
        info_df = pd.concat([df_prov, df_kota, df_kab], ignore_index=True).dropna(subset=['pemda'])
        parameter_df = read_and_clean_sheet(xls, "PARAMETER")
        kinerja_prov_df = read_and_clean_sheet(xls, "KINERJA_PROV")
        return info_df, parameter_df, kinerja_prov_df # Hanya memuat yang perlu untuk tes

    # Memanggil fungsi loader
    info, parameter, kinerja = load_data_from_excel()
    
    if info is not None and parameter is not None and kinerja is not None:
        st.success("Semua data yang diperlukan untuk tes berhasil dimuat!")
    else:
        st.error("Gagal memuat salah satu data. Proses dihentikan.")
        st.stop()

    st.write("Data berhasil dimuat. Mencoba membuat tab...")
    tab1, tab2, tab3 = st.tabs(["Informasi", "Provinsi", "Kabupaten/Kota"])

    with tab2:
        st.header("Tes Tab Provinsi")
        st.write("Berhasil masuk ke dalam blok 'with tab2'.")
        
        st.write("Mencoba membuat sidebar header...")
        st.sidebar.header("Filter Provinsi (Tes)")
        st.write("BERHASIL MEMBUAT SIDEBAR HEADER.")
        
        st.sidebar.success("Sidebar berhasil muncul!")
        
        st.write("Mencoba mengambil daftar indikator...")
        # Baris yang kemungkinan error
        daftar_indikator = parameter['indeks kinerja'].dropna().unique()
        st.write("BERHASIL MENGAMBIL DAFTAR INDIKATOR.")
        st.write("Indikator yang ditemukan:", daftar_indikator)


except Exception as e:
    st.error("TERJADI ERROR FATAL:")
    st.exception(e)
