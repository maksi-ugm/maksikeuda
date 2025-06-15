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

# --- FUNGSI MEMUAT DATA (PENDEKATAN BARU & AMAN) ---
@st.cache_data
def load_data_from_excel(path="data.xlsx"):
    try:
        xls = pd.ExcelFile(path)

        # 1. Proses Sheet INFO
        df_info_raw = pd.read_excel(xls, "INFO", header=None)
        df_info_raw.columns = [f'col_{i}' for i in range(len(df_info_raw.columns))]
        df_prov = df_info_raw[['col_0', 'col_1']].copy(); df_prov.rename(columns={'col_0': 'klaster', 'col_1': 'pemda'}, inplace=True); df_prov['tingkat'] = 'provinsi'
        df_kota = df_info_raw[['col_3', 'col_4']].copy(); df_kota.rename(columns={'col_3': 'klaster', 'col_4': 'pemda'}, inplace=True); df_kota['tingkat'] = 'kota'
        df_kab = df_info_raw[['col_6', 'col_7']].copy(); df_kab.rename(columns={'col_6': 'klaster', 'col_7': 'pemda'}, inplace=True); df_kab['tingkat'] = 'kabupaten'
        info_df = pd.concat([df_prov, df_kota, df_kab], ignore_index=True).dropna(subset=['pemda'])
        info_df = info_df[info_df['pemda'] != 'PROVINSI']

        # 2. Proses Sheet PARAMETER tanpa membaca header sama sekali
        parameter_df = pd.read_excel(xls, "PARAMETER", header=None)

        # 3. Baca sheet data utama
        kinerja_prov_df = pd.read_excel(xls, "KINERJA_PROV")
        kondisi_prov_df = pd.read_excel(xls, "KONDISI_PROV")
        stat_prov_df = pd.read_excel(xls, "STAT_PROV")
        
        # Menyamakan nama kolom di stat_prov_df untuk konsistensi
        stat_prov_df.rename(columns={'INDIKATOR KINERJA': 'INDICATOR', 'INDIKATOR KONDISI': 'INDICATOR'}, inplace=True, errors='ignore')
        
        # Data kab/kota tidak kita proses dulu
        kinerja_kabkota_df = pd.DataFrame()
        kondisi_kabkota_df = pd.DataFrame()
        stat_kab_df = pd.DataFrame()

        return (info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, 
                kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df)

    except Exception as e:
        st.error(f"Terjadi error fatal saat memuat data: {e}.")
        return (None,) * 8

# --- MEMUAT DATA DI AWAL ---
data_tuple = load_data_from_excel()

# --- FUNGSI GRAFIK (DENGAN LOGIKA BARU) ---
def display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette):
    if not selected_pemda:
        st.warning("Silakan pilih minimal satu pemerintah daerah untuk menampilkan grafik.")
        return

    fig = go.Figure()
    colors = px.colors.qualitative.Plotly if color_palette == 'Default' else getattr(px.colors.qualitative, color_palette)
    
    # Flag untuk mengecek apakah ada data teks
    contains_text_data = False

    # Proses data utama pemda terlebih dahulu
    annotations_to_add = []
    for i, pemda in enumerate(selected_pemda):
        pemda_df = main_df[(main_df['PEMDA'] == pemda) & (main_df['INDICATOR'] == selected_indikator)].copy()
        if pemda_df.empty: continue
        
        pemda_df['NILAI_NUMERIC'] = pd.to_numeric(pemda_df['NILAI'], errors='coerce')
        numeric_data = pemda_df.dropna(subset=['NILAI_NUMERIC'])
        text_data = pemda_df[pemda_df['NILAI_NUMERIC'].isna()]

        if not text_data.empty:
            contains_text_data = True
            for _, row in text_data.iterrows():
                annotations_to_add.append(dict(x=row['TIME'], y=0, yref="y", text=f"{pemda}:<br>{row['NILAI']}", showarrow=True, arrowhead=1, ax=0, ay=-40))
        
        if not numeric_data.empty:
            color = colors[i % len(colors)]
            df_plot = numeric_data.sort_values('TIME')
            if chart_type == 'Garis': fig.add_trace(go.Scatter(x=df_plot['TIME'], y=df_plot['NILAI_NUMERIC'], mode='lines+markers', name=pemda, line=dict(color=color), marker=dict(color=color)))
            elif chart_type == 'Area': fig.add_trace(go.Scatter(x=df_plot['TIME'], y=df_plot['NILAI_NUMERIC'], mode='lines', name=pemda, line=dict(color=color), fill='tozeroy'))
            elif chart_type == 'Batang': fig.add_trace(go.Bar(x=df_plot['TIME'], y=df_plot['NILAI_NUMERIC'], name=pemda, marker_color=color))

    # --- LOGIKA BARU: Hanya tampilkan statistik jika tidak ada data teks ---
    if not contains_text_data:
        stat_filtered = stat_df[(stat_df['KLASTER'] == selected_klaster) & (stat_df['INDICATOR'] == selected_indikator)]
        if not stat_filtered.empty:
            try:
                stat_pivot = stat_filtered.pivot(index='TIME', columns='STATISTIK', values='NILAI').reset_index()
                stat_pivot.columns = stat_pivot.columns.str.upper()
                stat_pivot = stat_pivot.sort_values('TIME')
                fig.add_trace(go.Scatter(x=stat_pivot['TIME'], y=stat_pivot['MIN'], mode='lines', line=dict(width=0), hoverinfo='none', showlegend=False))
                fig.add_trace(go.Scatter(x=stat_pivot['TIME'], y=stat_pivot['MAX'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(200, 200, 200, 0.3)', hoverinfo='none', name='Rentang Klaster (Min-Max)', showlegend=True ))
                fig.add_trace(go.Scatter(x=stat_pivot['TIME'], y=stat_pivot['MEDIAN'], mode='lines', line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'), name='Median Klaster', hoverinfo='x+y'))
            except Exception:
                 pass 

    for ann in annotations_to_add: fig.add_annotation(ann)

    fig.update_layout(title=f'<b>{selected_indikator}</b>', xaxis_title='Tahun', yaxis_title='Nilai', template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    
    if not contains_text_data:
        st.info("""**Keterangan Grafik:**\n- **Area Abu-abu:** Rentang nilai (Min-Max) klaster.\n- **Garis Putus-putus:** Nilai tengah (Median) klaster.""")

# --- FUNGSI UNTUK MEMBUAT TAB ANALISIS ---
def create_analysis_tab(level, info_df, parameter_df, kinerja_df, kondisi_df, stat_df):
    
    filter_col, chart_col = st.columns([1, 3])

    with filter_col:
        st.header(f"Filter {level}")
        color_palette = st.selectbox("Pilih Palet Warna", ['Default', 'G10', 'T10', 'Pastel', 'Dark2'], key=f'color_{level.lower()}')
        chart_type = st.radio("Pilih Tipe Grafik", ('Garis', 'Batang', 'Area'), key=f'chart_{level.lower()}')
        pilihan_data = st.radio("Pilih Jenis Data", ('Kinerja', 'Kondisi'), key=f'data_type_{level.lower()}')
        
        # Logika baru berdasarkan posisi kolom dan baris
        kinerja_col_idx, kondisi_col_idx, deskripsi_col_idx = 0, 2, 1

        if pilihan_data == 'Kondisi':
            main_df = kondisi_df
            # Baris 2-7 di Excel adalah index 1 sampai 6 di pandas
            daftar_indikator = parameter_df.iloc[1:7, kondisi_col_idx].dropna().unique()
        else: # Kinerja
            main_df = kinerja_df
            # Baris 2-7 di Excel adalah index 1 sampai 6 di pandas (sesuai screenshot)
            daftar_indikator = parameter_df.iloc[1:7, kinerja_col_idx].dropna().unique()

        selected_indikator = st.selectbox("Pilih Indikator", daftar_indikator, key=f'indikator_{level.lower()}')
        
        info_level_df = info_df[info_df['tingkat'] == 'provinsi']
        
        daftar_klaster = sorted(info_level_df['klaster'].dropna().unique())
        selected_klaster = st.selectbox("Pilih Klaster", daftar_klaster, key=f'klaster_{level.lower()}')
        
        daftar_pemda = sorted(info_level_df[info_level_df['klaster'] == selected_klaster]['pemda'].dropna().unique())
        selected_pemda = st.multiselect(f"Pilih {level}", daftar_pemda, key=f'pemda_{level.lower()}')

    with chart_col:
        if selected_indikator and selected_klaster:
            display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette)
            
            st.markdown("---")
            st.markdown(f"### Deskripsi Indikator: {selected_indikator}")
            
            # Cari deskripsi berdasarkan indikator yang dipilih
            # Cek di kedua kolom indikator (kinerja dan kondisi)
            desc_text = "Deskripsi untuk indikator ini tidak tersedia."
            for col_idx in [kinerja_col_idx, kondisi_col_idx]:
                mask = parameter_df.iloc[:, col_idx] == selected_indikator
                if mask.any():
                    deskripsi_row = parameter_df.loc[mask]
                    if not deskripsi_row.empty:
                        deskripsi = deskripsi_row.iloc[0, deskripsi_col_idx]
                        if pd.notna(deskripsi) and deskripsi:
                            desc_text = deskripsi
                        break
            st.info(desc_text)
        else:
            st.info(f"Silakan lengkapi semua filter di kolom kiri untuk menampilkan data.")

# --- STRUKTUR UTAMA APLIKASI ---
st.title("📊 Dashboard Kinerja & Kondisi Keuangan Pemerintah Daerah")

if data_tuple is None or data_tuple[0] is None:
    st.stop()

info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, _, _, _ = data_tuple

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
