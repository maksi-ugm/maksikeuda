import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard Keuangan & Kinerja Pemda",
    page_icon="📊"
)

# --- FUNGSI UNTUK MEMUAT DATA DARI FILE EXCEL ---
@st.cache_data
def load_data_from_excel(path="data.xlsx"):
    """Memuat semua data dari sheet di dalam satu file Excel."""
    try:
        xls = pd.ExcelFile(path)
        
        # Membaca setiap sheet yang diperlukan
        info_df = pd.read_excel(xls, "INFO")
        parameter_df = pd.read_excel(xls, "PARAMETER")
        kinerja_prov_df = pd.read_excel(xls, "KINERJA_PROV")
        kondisi_prov_df = pd.read_excel(xls, "KONDISI_PROV")
        stat_prov_df = pd.read_excel(xls, "STAT_PROV")
        kinerja_kab_df = pd.read_excel(xls, "KIN_KAB") # Sesuai nama file sebelumnya
        kondisi_kab_df = pd.read_excel(xls, "KONDISI_KAB") # Sesuai nama file sebelumnya
        stat_kab_df = pd.read_excel(xls, "STAT_KAB") # Sesuai nama file sebelumnya
        
        # Menggabungkan data Kab & Kota untuk kemudahan
        kinerja_kabkota_df = pd.concat([kinerja_kab_df, kondisi_kab_df[kinerja_kab_df.columns]], ignore_index=True)
        kondisi_kabkota_df = pd.concat([kondisi_kab_df, kinerja_kab_df[kondisi_kab_df.columns]], ignore_index=True)

        return (info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, 
                kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df)
    except FileNotFoundError:
        st.error(f"Error: File '{path}' tidak ditemukan. Pastikan file 'data.xlsx' ada di repository Anda.")
        return (None,) * 8
    except ValueError as e:
        # Error ini akan muncul jika nama sheet salah
        st.error(f"Error saat membaca sheet dari Excel: {e}. Pastikan nama sheet sudah benar (e.g., 'INFO', 'PARAMETER', dll).")
        return (None,) * 8


# --- MEMUAT DATA DI AWAL ---
(info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df,
 kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df) = load_data_from_excel()


# --- FUNGSI UNTUK GRAFIK (TIDAK ADA PERUBAHAN) ---
def display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df):
    """Membuat dan menampilkan grafik Plotly dengan area statistik klaster."""
    if not selected_pemda:
        st.warning("Silakan pilih minimal satu pemerintah daerah untuk menampilkan grafik.")
        return

    fig = go.Figure()
    stat_filtered = stat_df[(stat_df['Klaster'] == selected_klaster) & (stat_df['Indikator'] == selected_indikator)]
    
    if not stat_filtered.empty:
        stat_filtered = stat_filtered.sort_values('Tahun')
        fig.add_trace(go.Scatter(x=stat_filtered['Tahun'], y=stat_filtered['Min'], mode='lines', line=dict(width=0), hoverinfo='none', showlegend=False))
        fig.add_trace(go.Scatter(x=stat_filtered['Tahun'], y=stat_filtered['Max'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(200, 200, 200, 0.3)', hoverinfo='none', name='Rentang Klaster (Min-Max)', showlegend=True ))
        fig.add_trace(go.Scatter(x=stat_filtered['Tahun'], y=stat_filtered['Median'], mode='lines', line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'), name='Median Klaster', hoverinfo='x+y'))

    for pemda in selected_pemda:
        pemda_df = main_df[(main_df['Pemda'] == pemda) & (main_df['Indikator'] == selected_indikator)].sort_values('Tahun')
        if not pemda_df.empty:
            fig.add_trace(go.Scatter(x=pemda_df['Tahun'], y=pemda_df['Nilai'], mode='lines+markers', name=pemda, hovertemplate=f'<b>{pemda}</b><br>Tahun: %{{x}}<br>Nilai: %{{y}}<extra></extra>'))

    fig.update_layout(title=f'<b>{selected_indikator}</b>', xaxis_title='Tahun', yaxis_title='Nilai', template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    st.info("""**Keterangan Grafik:**\n- **Area Abu-abu:** Menunjukkan rentang nilai (Minimum-Maksimum) dari semua pemerintah daerah dalam klaster yang dipilih.\n- **Garis Putus-putus:** Menunjukkan nilai tengah (Median) dari klaster tersebut.""")


# --- FUNGSI UNTUK MEMBUAT TAB ANALISIS (TIDAK ADA PERUBAHAN) ---
def create_analysis_tab(level, info_df, parameter_df, kinerja_df, kondisi_df, stat_df):
    """Membuat seluruh konten untuk tab analisis, termasuk sidebar dan grafik."""
    st.sidebar.header(f"Filter {level}")
    pilihan_data = st.sidebar.radio("Pilih Jenis Data", ('Kinerja', 'Kondisi'), key=f'data_type_{level.lower()}')
    
    if pilihan_data == 'Kinerja':
        main_df = kinerja_df
        daftar_indikator = parameter_df.iloc[0:6]['Indikator Kinerja'].dropna().unique()
    else:
        main_df = kondisi_df
        daftar_indikator = parameter_df.iloc[6:13]['Indikator Kinerja'].dropna().unique()
    selected_indikator = st.sidebar.selectbox("Pilih Indikator", daftar_indikator, key=f'indikator_{level.lower()}')
    
    if level == 'Provinsi':
        info_level_df = info_df[info_df['Tingkat'] == 'Provinsi']
    else:
        info_level_df = info_df[info_df['Tingkat'].isin(['Kabupaten', 'Kota'])]
    daftar_klaster = sorted(info_level_df['Klaster'].dropna().unique())
    selected_klaster = st.sidebar.selectbox("Pilih Klaster", daftar_klaster, key=f'klaster_{level.lower()}')
    
    daftar_pemda = sorted(info_level_df[info_level_df['Klaster'] == selected_klaster]['Pemda'].dropna().unique())
    selected_pemda = st.sidebar.multiselect(f"Pilih {level}", daftar_pemda, key=f'pemda_{level.lower()}')
    
    if selected_indikator and selected_klaster:
        display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df)
    else:
        st.info(f"Silakan lengkapi semua filter di sidebar untuk menampilkan data {level}.")

# --- STRUKTUR UTAMA APLIKASI ---
st.title("📊 Dashboard Kinerja & Kondisi Keuangan Pemerintah Daerah")

if info_df is None:
    st.stop()

tab1, tab2, tab3 = st.tabs(["**Informasi**", "**Provinsi**", "**Kabupaten/Kota**"])

with tab1:
    st.header("Informasi Klaster Pemerintah Daerah")
    st.markdown("Gunakan kotak pencarian untuk menemukan pemerintah daerah di dalam setiap klaster.")
    for tingkat in ['Provinsi', 'Kabupaten', 'Kota']:
        st.subheader(f"Klaster {tingkat}")
        df_tingkat = info_df[info_df['Tingkat'] == tingkat][['Pemda', 'Klaster']].reset_index(drop=True)
        search_term = st.text_input(f"Cari {tingkat}...", key=f"search_{tingkat.lower()}")
        if search_term:
            df_display = df_tingkat[df_tingkat['Pemda'].str.contains(search_term, case=False)]
        else:
            df_display = df_tingkat
        st.dataframe(df_display, use_container_width=True, hide_index=True)

with tab2:
    create_analysis_tab("Provinsi", info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df)

with tab3:
    create_analysis_tab("Kabupaten/Kota", info_df, parameter_df, kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df)
