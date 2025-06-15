import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard Kinerja & Kondisi Keuangan Pemerintah Daerah",
    page_icon="📊"
)

# --- KODE KUSTOMISASI TAMPILAN ---
hide_st_ui = r"""
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

# --- FUNGSI MEMUAT DATA (VERSI FINAL SESUAI DATA ASLI) ---
@st.cache_data
def load_data_from_excel(path="data.xlsx"):
    try:
        xls = pd.ExcelFile(path)

        # 1. Proses Sheet INFO (tetap diubah ke lowercase untuk konsistensi internal)
        df_info_raw = pd.read_excel(xls, "INFO")
        df_info_raw.columns = df_info_raw.columns.str.strip().str.lower()
        df_prov = df_info_raw[['klaster', 'provinsi']].copy(); df_prov.rename(columns={'provinsi': 'pemda'}, inplace=True); df_prov['tingkat'] = 'provinsi'
        df_kota = df_info_raw[['klaster.1', 'kota']].copy(); df_kota.rename(columns={'klaster.1': 'klaster', 'kota': 'pemda'}, inplace=True); df_kota['tingkat'] = 'kota'
        df_kab = df_info_raw[['klaster.2', 'kabupaten']].copy(); df_kab.rename(columns={'klaster.2': 'klaster', 'kabupaten': 'pemda'}, inplace=True); df_kab['tingkat'] = 'kabupaten'
        info_df = pd.concat([df_prov, df_kota, df_kab], ignore_index=True).dropna(subset=['pemda'])

        # 2. Proses Sheet PARAMETER
        df_param_raw = pd.read_excel(xls, "PARAMETER")
        # Ambil kolom berdasarkan nama aslinya
        kinerja_desc = df_param_raw[['INDEKS KINERJA', 'Unnamed: 1']].copy().dropna(subset=['INDEKS KINERJA'])
        kinerja_desc.rename(columns={'INDEKS KINERJA': 'INDIKATOR', 'Unnamed: 1': 'DESKRIPSI'}, inplace=True)
        kondisi_desc = df_param_raw[['INDEKS KONDISI', 'Unnamed: 1']].copy().dropna(subset=['INDEKS KONDISI'])
        kondisi_desc.rename(columns={'INDEKS KONDISI': 'INDIKATOR', 'Unnamed: 1': 'DESKRIPSI'}, inplace=True)
        parameter_df = pd.concat([kinerja_desc, kondisi_desc], ignore_index=True)

        # 3. Baca sheet lain tanpa mengubah nama kolom (tetap KAPITAL)
        kinerja_prov_df = pd.read_excel(xls, "KINERJA_PROV")
        kondisi_prov_df = pd.read_excel(xls, "KONDISI_PROV")
        stat_prov_df = pd.read_excel(xls, "STAT_PROV")
        
        # Data kab/kota tidak kita pakai dulu, tapi tetap dimuat
        kinerja_kab_df = pd.read_excel(xls, "KIN_KAB")
        kondisi_kab_df = pd.read_excel(xls, "KONDISI_KAB")
        stat_kab_df = pd.read_excel(xls, "STAT_KAB")
        kinerja_kabkota_df = pd.concat([kinerja_kab_df, kondisi_kab_df.reindex(columns=kinerja_kab_df.columns)], ignore_index=True)
        kondisi_kabkota_df = pd.concat([kondisi_kab_df, kinerja_kab_df.reindex(columns=kondisi_kab_df.columns)], ignore_index=True)

        return (info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, 
                kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df)

    except Exception as e:
        st.error(f"Terjadi error fatal saat memuat data: {e}. Periksa file 'data.xlsx' dan nama-nama sheet-nya.")
        return (None,) * 8

# --- MEMUAT DATA DI AWAL ---
data_tuple = load_data_from_excel()

# --- FUNGSI UNTUK GRAFIK (MENGGUNAKAN KOLOM KAPITAL) ---
def display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette):
    if not selected_pemda:
        st.warning("Silakan pilih minimal satu pemerintah daerah untuk menampilkan grafik.")
        return

    fig = go.Figure()
    colors = px.colors.qualitative.Plotly if color_palette == 'Default' else getattr(px.colors.qualitative, color_palette)

    stat_filtered = stat_df[(stat_df['KLASTER'] == selected_klaster) & (stat_df['INDIKATOR'] == selected_indikator)]
    if not stat_filtered.empty:
        stat_filtered = stat_filtered.sort_values('TAHUN')
        fig.add_trace(go.Scatter(x=stat_filtered['TAHUN'], y=stat_filtered['MIN'], mode='lines', line=dict(width=0), hoverinfo='none', showlegend=False))
        fig.add_trace(go.Scatter(x=stat_filtered['TAHUN'], y=stat_filtered['MAX'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(200, 200, 200, 0.3)', hoverinfo='none', name='Rentang Klaster (Min-Max)', showlegend=True ))
        fig.add_trace(go.Scatter(x=stat_filtered['TAHUN'], y=stat_filtered['MEDIAN'], mode='lines', line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'), name='Median Klaster', hoverinfo='x+y'))

    for i, pemda in enumerate(selected_pemda):
        pemda_df = main_df[(main_df['PEMDA'] == pemda) & (main_df['INDIKATOR'] == selected_indikator)].sort_values('TAHUN')
        if pemda_df.empty: continue
        color = colors[i % len(colors)]
        if chart_type == 'Garis': fig.add_trace(go.Scatter(x=pemda_df['TAHUN'], y=pemda_df['NILAI'], mode='lines+markers', name=pemda, line=dict(color=color), marker=dict(color=color)))
        elif chart_type == 'Area': fig.add_trace(go.Scatter(x=pemda_df['TAHUN'], y=pemda_df['NILAI'], mode='lines', name=pemda, line=dict(color=color), fill='tozeroy'))
        elif chart_type == 'Batang': fig.add_trace(go.Bar(x=pemda_df['TAHUN'], y=pemda_df['NILAI'], name=pemda, marker_color=color))

    fig.update_layout(title=f'<b>{selected_indikator}</b>', xaxis_title='Tahun', yaxis_title='Nilai', template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    st.info("""**Keterangan Grafik:**\n- **Area Abu-abu:** Rentang nilai (Min-Max) klaster.\n- **Garis Putus-putus:** Nilai tengah (Median) klaster.""")

# --- FUNGSI UNTUK MEMBUAT TAB ANALISIS ---
def create_analysis_tab(level, info_df, parameter_df, kinerja_df, kondisi_df, stat_df):
    filter_col, chart_col = st.columns([1, 3])

    with filter_col:
        st.header(f"Filter {level}")
        color_palette = st.selectbox("Pilih Palet Warna", ['Default', 'G10', 'T10', 'Pastel', 'Dark2'], key=f'color_{level.lower()}')
        chart_type = st.radio("Pilih Tipe Grafik", ('Garis', 'Batang', 'Area'), key=f'chart_{level.lower()}')
        pilihan_data = st.radio("Pilih Jenis Data", ('Kinerja', 'Kondisi'), key=f'data_type_{level.lower()}')
        
        kinerja_list = parameter_df[parameter_df['INDIKATOR'].str.contains('Kinerja', case=False, na=False)]['INDIKATOR'].unique()
        kondisi_list = parameter_df[parameter_df['INDIKATOR'].str.contains('Kondisi', case=False, na=False)]['INDIKATOR'].unique()

        if pilihan_data == 'Kondisi':
            main_df, daftar_indikator = kondisi_df, kondisi_list
        else: 
            main_df, daftar_indikator = kinerja_df, kinerja_list

        selected_indikator = st.selectbox("Pilih Indikator", daftar_indikator, key=f'indikator_{level.lower()}')
        
        if level == 'Provinsi': info_level_df = info_df[info_df['tingkat'] == 'provinsi']
        else: info_level_df = info_df[info_df['tingkat'].isin(['kabupaten', 'kota'])]
        
        daftar_klaster = sorted(info_level_df['klaster'].dropna().unique())
        selected_klaster = st.selectbox("Pilih Klaster", daftar_klaster, key=f'klaster_{level.lower()}')
        
        daftar_pemda = sorted(info_level_df[info_level_df['klaster'] == selected_klaster]['pemda'].dropna().unique())
        selected_pemda = st.multiselect(f"Pilih {level}", daftar_pemda, key=f'pemda_{level.lower()}')

    with chart_col:
        if selected_indikator and selected_klaster:
            display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette)
            
            st.markdown("---")
            st.markdown(f"### Deskripsi Indikator: {selected_indikator}")
            
            deskripsi_row = parameter_df.loc[parameter_df['INDIKATOR'] == selected_indikator]
            if not deskripsi_row.empty:
                deskripsi = deskripsi_row['DESKRIPSI'].iloc[0]
                if pd.notna(deskripsi) and deskripsi:
                    st.info(deskripsi)
                else:
                    st.info("Deskripsi untuk indikator ini tidak tersedia.")
            else:
                st.info("Deskripsi untuk indikator ini tidak tersedia.")
        else:
            st.info(f"Silakan lengkapi semua filter di kolom kiri untuk menampilkan data.")

# --- STRUKTUR UTAMA APLIKASI ---
st.title("📊 Dashboard Kinerja & Kondisi Keuangan Pemerintah Daerah")

if data_tuple[0] is None:
    st.stop()

info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df = data_tuple

tab1, tab2 = st.tabs(["**Informasi**", "**Provinsi**"])

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

# --- FOOTER CUSTOM ---
st.markdown("---")
st.markdown("Dibuat oleh **Kelas MAKSI UGM**")
