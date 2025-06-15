import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- KONFIGURASI HALAMAN (HARUS MENJADI PERINTAH STREAMLIT PERTAMA) ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard Kinerja & Kondisi Keuangan Pemerintah Daerah",
    page_icon="📊"
)

# --- KODE UNTUK KUSTOMISASI TAMPILAN (FOOTER, DLL) ---
hide_st_ui = """
            <style>
            div[data-testid="stToolbar"] {visibility: hidden;}
            div[data-testid="stDecoration"] {visibility: hidden;}
            div[data-testid="stStatusWidget"] {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_ui, unsafe_allow_html=True) 

# --- FUNGSI UNTUK MEMUAT DATA (VERSI PALING ROBUST) ---
@st.cache_data
def load_data_from_excel(path="data.xlsx"):
    """Memuat semua data, mentransformasi INFO, dan membersihkan semua nama kolom."""
    try:
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
        kondisi_prov_df = read_and_clean_sheet(xls, "KONDISI_PROV")
        stat_prov_df = read_and_clean_sheet(xls, "STAT_PROV")
        kinerja_kab_df = read_and_clean_sheet(xls, "KIN_KAB")
        kondisi_kab_df = read_and_clean_sheet(xls, "KONDISI_KAB")
        stat_kab_df = read_and_clean_sheet(xls, "STAT_KAB")
        
        kinerja_kabkota_df = pd.concat([kinerja_kab_df, kondisi_kab_df[kinerja_kab_df.columns]], ignore_index=True)
        kondisi_kabkota_df = pd.concat([kondisi_kab_df, kinerja_kab_df[kondisi_kab_df.columns]], ignore_index=True)

        return (info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, 
                kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df)
    except Exception as e:
        st.error(f"Terjadi error fatal saat memuat data: {e}. Pastikan file 'data.xlsx' dan semua sheet di dalamnya (INFO, PARAMETER, dll) ada dan sesuai format.")
        return (None,) * 8

# --- MEMUAT DATA DI AWAL ---
(info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df,
 kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df) = load_data_from_excel()


# --- FUNGSI UNTUK GRAFIK (DENGAN FITUR BARU) ---
def display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette):
    if not selected_pemda:
        st.warning("Silakan pilih minimal satu pemerintah daerah untuk menampilkan grafik.")
        return

    fig = go.Figure()
    
    # Ambil palet warna dari Plotly Express
    colors = px.colors.qualitative.Plotly if color_palette == 'Default' else getattr(px.colors.qualitative, color_palette)

    # 1. Gambar data statistik klaster (Area Min-Max dan Garis Median)
    stat_filtered = stat_df[(stat_df['klaster'] == selected_klaster) & (stat_df['indikator'] == selected_indikator)]
    if not stat_filtered.empty:
        stat_filtered = stat_filtered.sort_values('tahun')
        fig.add_trace(go.Scatter(x=stat_filtered['tahun'], y=stat_filtered['min'], mode='lines', line=dict(width=0), hoverinfo='none', showlegend=False))
        fig.add_trace(go.Scatter(x=stat_filtered['tahun'], y=stat_filtered['max'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(200, 200, 200, 0.3)', hoverinfo='none', name='Rentang Klaster (Min-Max)', showlegend=True ))
        fig.add_trace(go.Scatter(x=stat_filtered['tahun'], y=stat_filtered['median'], mode='lines', line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'), name='Median Klaster', hoverinfo='x+y'))

    # 2. Gambar data Pemda yang dipilih sesuai tipe grafik
    for i, pemda in enumerate(selected_pemda):
        pemda_df = main_df[(main_df['pemda'] == pemda) & (main_df['indikator'] == selected_indikator)].sort_values('tahun')
        if pemda_df.empty:
            continue
        
        color = colors[i % len(colors)] # Pilih warna secara berulang dari palet

        if chart_type == 'Garis':
            fig.add_trace(go.Scatter(x=pemda_df['tahun'], y=pemda_df['nilai'], mode='lines+markers', name=pemda, line=dict(color=color), marker=dict(color=color)))
        elif chart_type == 'Area':
            fig.add_trace(go.Scatter(x=pemda_df['tahun'], y=pemda_df['nilai'], mode='lines', name=pemda, line=dict(color=color), fill='tozeroy'))
        elif chart_type == 'Batang':
            fig.add_trace(go.Bar(x=pemda_df['tahun'], y=pemda_df['nilai'], name=pemda, marker_color=color))

    fig.update_layout(title=f'<b>{selected_indikator}</b>', xaxis_title='Tahun', yaxis_title='Nilai', template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    st.info("""**Keterangan Grafik:**\n- **Area Abu-abu:** Menunjukkan rentang nilai (Minimum-Maksimum) dari semua pemerintah daerah dalam klaster yang dipilih.\n- **Garis Putus-putus:** Menunjukkan nilai tengah (Median) dari klaster tersebut.""")

# --- FUNGSI UNTUK MEMBUAT TAB ANALISIS (DENGAN FITUR BARU) ---
def create_analysis_tab(level, info_df, parameter_df, kinerja_df, kondisi_df, stat_df):
    st.sidebar.header(f"Filter {level}")

    # FITUR BARU: Pilih Palet Warna
    color_palette = st.sidebar.selectbox(
        "Pilih Palet Warna",
        ['Default', 'G10', 'T10', 'Pastel', 'Dark2'],
        key=f'color_{level.lower()}'
    )

    # FITUR BARU: Pilih Tipe Grafik
    chart_type = st.sidebar.radio(
        "Pilih Tipe Grafik",
        ('Garis', 'Batang', 'Area'),
        key=f'chart_{level.lower()}'
    )
    
    pilihan_data = st.sidebar.radio("Pilih Jenis Data", ('Kinerja', 'Kondisi'), key=f'data_type_{level.lower()}')
    
    if pilihan_data == 'Kinerja':
        main_df = kinerja_df
        daftar_indikator = parameter_df['indeks kinerja'].dropna().unique()
    else: 
        main_df = kondisi_df
        daftar_indikator = parameter_df['indeks kondisi'].dropna().unique()

    selected_indikator = st.sidebar.selectbox("Pilih Indikator", daftar_indikator, key=f'indikator_{level.lower()}')
    
    if level == 'Provinsi': info_level_df = info_df[info_df['tingkat'] == 'provinsi']
    else: info_level_df = info_df[info_df['tingkat'].isin(['kabupaten', 'kota'])]
    
    daftar_klaster = sorted(info_level_df['klaster'].dropna().unique())
    selected_klaster = st.sidebar.selectbox("Pilih Klaster", daftar_klaster, key=f'klaster_{level.lower()}')
    
    daftar_pemda = sorted(info_level_df[info_level_df['klaster'] == selected_klaster]['pemda'].dropna().unique())
    selected_pemda = st.sidebar.multiselect(f"Pilih {level}", daftar_pemda, key=f'pemda_{level.lower()}')
    
    if selected_indikator and selected_klaster:
        display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette)
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
    col1, col2, col3 = st.columns(3, gap="large")
    for i, tingkat in enumerate(['provinsi', 'kabupaten', 'kota']):
        with [col1, col2, col3][i]:
            st.subheader(f"Klaster {tingkat.capitalize()}")
            df_tingkat = info_df[info_df['tingkat'] == tingkat][['pemda', 'klaster']].reset_index(drop=True)
            label_pencarian = f"Cari {tingkat.capitalize()}..."
            search_term = st.text_input(label_pencarian, key=f"search_{tingkat}")
            if search_term: df_display = df_tingkat[df_tingkat['pemda'].str.contains(search_term, case=False)]
            else: df_display = df_tingkat
            st.dataframe(df_display, use_container_width=True, hide_index=True)

with tab2:
    create_analysis_tab("Provinsi", info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df)

with tab3:
    create_analysis_tab("Kabupaten/Kota", info_df, parameter_df, kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df)

# --- FOOTER CUSTOM ---
st.markdown("---")
st.markdown("Dibuat oleh **Kelas MAKSI UGM**")
