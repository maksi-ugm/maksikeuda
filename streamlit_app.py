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

# --- FUNGSI MEMUAT DATA ---
@st.cache_data
def load_data_from_excel(path="data.xlsx"):
    try:
        xls = pd.ExcelFile(path)
        info_df = pd.read_excel(xls, "INFO")
        parameter_df = pd.read_excel(xls, "PARAMETER")
        kinerja_prov_df = pd.read_excel(xls, "KINERJA_PROV")
        kondisi_prov_df = pd.read_excel(xls, "KONDISI_PROV")
        stat_prov_df = pd.read_excel(xls, "STAT_PROV")
        kinerja_kab_df = pd.read_excel(xls, "KIN_KAB")
        kondisi_kab_df = pd.read_excel(xls, "KONDISI_KAB")
        stat_kab_df = pd.read_excel(xls, "STAT_KAB")
        # --- PERUBAHAN 1: Memuat sheet 'TREN' ---
        tren_df = pd.read_excel(xls, "TREN")
        
        kinerja_kabkota_df = pd.concat([kinerja_kab_df, kondisi_kab_df], ignore_index=True)
        kondisi_kabkota_df = pd.concat([kondisi_kab_df, kinerja_kab_df], ignore_index=True)

        return (info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, 
                kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df, tren_df)

    except Exception as e:
        st.error(f"Terjadi error fatal saat memuat data: {e}.")
        # Pastikan jumlah return value sesuai
        return (None,) * 9

# --- MEMUAT DATA DI AWAL ---
data_tuple = load_data_from_excel()

# --- FUNGSI GRAFIK ---
# --- PERUBAHAN 2: Menambahkan tren_df sebagai argumen ---
def display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette, tingkat_filter, tren_df):
    if not selected_pemda:
        st.warning("Silakan pilih minimal satu pemerintah daerah untuk menampilkan grafik.")
        return

    fig = go.Figure()
    colors = px.colors.qualitative.Plotly if color_palette == 'Default' else getattr(px.colors.qualitative, color_palette)
    
    stat_filtered = stat_df[
        (stat_df['KLASTER'] == selected_klaster) & 
        (stat_df['INDIKATOR'] == selected_indikator) &
        (stat_df['TINGKAT'] == tingkat_filter)
    ]
    
    if not stat_filtered.empty:
        stat_filtered = stat_filtered.sort_values('TAHUN')
        if all(col in stat_filtered.columns for col in ['MIN', 'MAX', 'MEDIAN']):
            # Area Min-Max disembunyikan
            # fig.add_trace(go.Scatter(x=stat_filtered['TAHUN'], y=stat_filtered['MIN'], mode='lines', line=dict(width=0), hoverinfo='none', showlegend=False))
            # fig.add_trace(go.Scatter(x=stat_filtered['TAHUN'], y=stat_filtered['MAX'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(200, 200, 200, 0.3)', hoverinfo='none', name='Rentang Klaster (Min-Max)', showlegend=True ))
            
            fig.add_trace(go.Scatter(x=stat_filtered['TAHUN'], y=stat_filtered['MEDIAN'], mode='lines', line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'), name='Median Klaster', hoverinfo='x+y'))

    annotations_to_add = []
    for i, pemda in enumerate(selected_pemda):
        pemda_df = main_df[(main_df['PEMDA'] == pemda) & (main_df['INDIKATOR'] == selected_indikator)].copy()
        if pemda_df.empty: continue
        
        pemda_df['NILAI_NUMERIC'] = pd.to_numeric(pemda_df['NILAI'], errors='coerce')
        numeric_data = pemda_df.dropna(subset=['NILAI_NUMERIC'])
        text_data = pemda_df[pemda_df['NILAI_NUMERIC'].isna()]
        
        if not text_data.empty:
            for _, row in text_data.iterrows():
                annotations_to_add.append(dict(x=row['TAHUN'], y=0, yref="y", text=f"{pemda}:<br>{row['NILAI']}", showarrow=True, arrowhead=1, ax=0, ay=-40))
        
        if not numeric_data.empty:
            color = colors[i % len(colors)]
            df_plot = numeric_data.sort_values('TAHUN')
            if chart_type == 'Garis': fig.add_trace(go.Scatter(x=df_plot['TAHUN'], y=df_plot['NILAI_NUMERIC'], mode='lines+markers', name=pemda, line=dict(color=color), marker=dict(color=color)))
            elif chart_type == 'Area': fig.add_trace(go.Scatter(x=df_plot['TAHUN'], y=df_plot['NILAI_NUMERIC'], mode='lines', name=pemda, line=dict(color=color), fill='tozeroy'))
            elif chart_type == 'Batang': fig.add_trace(go.Bar(x=df_plot['TAHUN'], y=df_plot['NILAI_NUMERIC'], name=pemda, marker_color=color))

    for ann in annotations_to_add: fig.add_annotation(ann)

    fig.update_layout(title=f'<b>{selected_indikator}</b>', xaxis_title='Tahun', yaxis_title='Nilai', template='plotly_white', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("""**Keterangan Grafik:**\n- **Garis Putus-putus:** Nilai tengah (Median) klaster.""")

    # --- PERUBAHAN 3: Menambahkan blok Analisis Tren ---
    st.markdown("---")
    st.markdown("### Analisis Tren 3 Tahun Terakhir")

    if not selected_pemda:
        st.write("Pilih pemerintah daerah untuk melihat analisis tren.")
        return

    for pemda in selected_pemda:
        # Cari data tren untuk kombinasi indikator dan pemda yang dipilih
        tren_data = tren_df[
            (tren_df['INDIKATOR'] == selected_indikator) & 
            (tren_df['PEMDA'] == pemda)
        ]

        if not tren_data.empty:
            nilai_tren = tren_data['NILAI'].iloc[0]
            
            if nilai_tren.lower() == 'hijau':
                st.success(f"**Baik/Diharapkan (Favorable)**: Indikator **{selected_indikator}** pada **{pemda}** menunjukkan tren **kenaikan** pada 3 tahun terakhir.")
            elif nilai_tren.lower() == 'kuning':
                st.warning(f"**Tidak Pasti (Uncertain)**: Indikator **{selected_indikator}** pada **{pemda}** menunjukkan tren **fluktuasi** (naik dan turun) pada 3 tahun terakhir.")
            elif nilai_tren.lower() == 'merah':
                st.error(f"**Tidak Baik/Tidak Diharapkan (Unfavorable)**: Indikator **{selected_indikator}** pada **{pemda}** menunjukkan tren **penurunan** pada 3 tahun terakhir.")
        else:
            # Pesan jika data tren tidak ditemukan untuk pemda tersebut
            st.markdown(f"- Analisis tren untuk **{pemda}** pada indikator ini tidak tersedia.")


# --- FUNGSI UNTUK MEMBUAT TAB ANALISIS ---
# --- PERUBAHAN 4: Menambahkan tren_df sebagai argumen ---
def create_analysis_tab(level, info_df, parameter_df, kinerja_df, kondisi_df, stat_df, tren_df):
    filter_col, chart_col = st.columns([1, 3])

    with filter_col:
        st.header(f"Filter {level}")
        
        pilihan_tingkat = 'Provinsi'
        if level == 'Kabupaten/Kota':
            pilihan_tingkat = st.radio("Pilih Tingkat", ('Kabupaten', 'Kota'), key='tingkat_selector', horizontal=True)
            info_level_df = info_df[info_df['TINGKAT'] == pilihan_tingkat]
        else:
            info_level_df = info_df[info_df['TINGKAT'] == 'Provinsi']
            
        color_palette = st
