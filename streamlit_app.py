import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
# Mengatur konfigurasi halaman harus menjadi perintah pertama
st.set_page_config(
    layout="wide",
    page_title="Dashboard Keuangan & Kinerja Pemda",
    page_icon="📊"
)

# --- FUNGSI UNTUK MEMUAT DATA ---
@st.cache_data
def load_data():
    """Memuat semua data dari file CSV dan mengembalikannya sebagai dataframes."""
    try:
        info_df = pd.read_csv("data.xlsx - INFO.csv")
        parameter_df = pd.read_csv("data.xlsx - PARAMETER.csv")
        kinerja_prov_df = pd.read_csv("data.xlsx - KINERJA_PROV.csv")
        kondisi_prov_df = pd.read_csv("data.xlsx - KONDISI_PROV.csv")
        stat_prov_df = pd.read_csv("data.xlsx - STAT_PROV.csv")
        kinerja_kab_df = pd.read_csv("data.xlsx - KIN_KAB.csv")
        kondisi_kab_df = pd.read_csv("data.xlsx - KONDISI_KAB.csv")
        stat_kab_df = pd.read_csv("data.xlsx - STAT_KAB.csv")
        
        # Menggabungkan data Kab & Kota untuk kemudahan
        kinerja_kabkota_df = pd.concat([kinerja_kab_df, kondisi_kab_df[kinerja_kab_df.columns]], ignore_index=True)
        kondisi_kabkota_df = pd.concat([kondisi_kab_df, kinerja_kab_df[kondisi_kab_df.columns]], ignore_index=True)

        return (info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, 
                kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df)
    except FileNotFoundError as e:
        st.error(f"Error: File data tidak ditemukan. Pastikan file '{e.filename}' ada di repository Anda.")
        return (None,) * 8

# --- MEMUAT DATA DI AWAL ---
(info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df,
 kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df) = load_data()


# --- FUNGSI UNTUK GRAFIK ---
def display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df):
    """Membuat dan menampilkan grafik Plotly dengan area statistik klaster."""
    if not selected_pemda:
        st.warning("Silakan pilih minimal satu pemerintah daerah untuk menampilkan grafik.")
        return

    fig = go.Figure()

    # 1. Ambil dan gambar data statistik klaster (Area Min-Max dan Garis Median)
    stat_filtered = stat_df[(stat_df['Klaster'] == selected_klaster) & (stat_df['Indikator'] == selected_indikator)]
    
    if not stat_filtered.empty:
        # Urutkan berdasarkan tahun
        stat_filtered = stat_filtered.sort_values('Tahun')
        
        fig.add_trace(go.Scatter(
            x=stat_filtered['Tahun'],
            y=stat_filtered['Min'],
            mode='lines',
            line=dict(width=0),
            hoverinfo='none',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=stat_filtered['Tahun'],
            y=stat_filtered['Max'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(200, 200, 200, 0.3)',
            hoverinfo='none',
            name='Rentang Klaster (Min-Max)',
            showlegend=True 
        ))
        fig.add_trace(go.Scatter(
            x=stat_filtered['Tahun'],
            y=stat_filtered['Median'],
            mode='lines',
            line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'),
            name='Median Klaster',
            hoverinfo='x+y'
        ))

    # 2. Gambar data Pemda yang dipilih
    for pemda in selected_pemda:
        pemda_df = main_df[(main_df['Pemda'] == pemda) & (main_df['Indikator'] == selected_indikator)].sort_values('Tahun')
        if not pemda_df.empty:
            fig.add_trace(go.Scatter(
                x=pemda_df['Tahun'],
                y=pemda_df['Nilai'],
                mode='lines+markers',
                name=pemda,
                hovertemplate=f'<b>{pemda}</b><br>Tahun: %{{x}}<br>Nilai: %{{y}}<extra></extra>'
            ))

    # 3. Kustomisasi Tampilan Grafik
    fig.update_layout(
        title=f'<b>{selected_indikator}</b>',
        xaxis_title='Tahun',
        yaxis_title='Nilai',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info("""
    **Keterangan Grafik:**
    - **Area Abu-abu:** Menunjukkan rentang nilai (dari terendah/Minimum hingga tertinggi/Maksimum) dari semua pemerintah daerah dalam klaster yang dipilih.
    - **Garis Putus-putus:** Menunjukkan nilai tengah (Median) dari klaster tersebut.
    """)


# --- FUNGSI UNTUK MEMBUAT TAB ANALISIS (PROV & KAB/KOTA) ---
def create_analysis_tab(level, info_df, parameter_df, kinerja_df, kondisi_df, stat_df):
    """Membuat seluruh konten untuk tab analisis, termasuk sidebar dan grafik."""
    
    st.sidebar.header(f"Filter {level}")

    # 1. Pilih Kinerja atau Kondisi
    pilihan_data = st.sidebar.radio(
        "Pilih Jenis Data",
        ('Kinerja', 'Kondisi'),
        key=f'data_type_{level.lower()}'
    )

    # 2. Pilih Indikator (dinamis berdasarkan pilihan_data)
    if pilihan_data == 'Kinerja':
        main_df = kinerja_df
        daftar_indikator = parameter_df.iloc[0:6]['Indikator Kinerja'].dropna().unique()
    else: # Kondisi
        main_df = kondisi_df
        daftar_indikator = parameter_df.iloc[6:13]['Indikator Kinerja'].dropna().unique()

    selected_indikator = st.sidebar.selectbox(
        "Pilih Indikator",
        daftar_indikator,
        key=f'indikator_{level.lower()}'
    )
    
    # 3. Pilih Klaster
    if level == 'Provinsi':
        info_level_df = info_df[info_df['Tingkat'] == 'Provinsi']
    else: # Kabupaten/Kota
        info_level_df = info_df[info_df['Tingkat'].isin(['Kabupaten', 'Kota'])]

    daftar_klaster = sorted(info_level_df['Klaster'].dropna().unique())
    selected_klaster = st.sidebar.selectbox(
        "Pilih Klaster",
        daftar_klaster,
        key=f'klaster_{level.lower()}'
    )

    # 4. Pilih Pemerintah Daerah (dinamis berdasarkan klaster)
    daftar_pemda = sorted(info_level_df[info_level_df['Klaster'] == selected_klaster]['Pemda'].dropna().unique())
    selected_pemda = st.sidebar.multiselect(
        f"Pilih {level}",
        daftar_pemda,
        key=f'pemda_{level.lower()}'
    )
    
    # Tampilkan grafik di area utama
    if selected_indikator and selected_klaster:
        display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df)
    else:
        st.info(f"Silakan lengkapi semua filter di sidebar untuk menampilkan data {level}.")


# --- STRUKTUR UTAMA APLIKASI ---
st.title("📊 Dashboard Keuangan & Kinerja Pemerintah Daerah")

# Cek apakah data berhasil dimuat
if info_df is None:
    st.stop()

# Definisi Tab
tab1, tab2, tab3 = st.tabs(["**Informasi**", "**Provinsi**", "**Kabupaten/Kota**"])


# --- KONTEN TAB 1: INFORMASI ---
with tab1:
    st.header("Informasi Klaster Pemerintah Daerah")
    st.markdown("Gunakan kotak pencarian untuk menemukan pemerintah daerah di dalam setiap klaster.")

    for tingkat in ['Provinsi', 'Kabupaten', 'Kota']:
        st.subheader(f"Klaster {tingkat}")
        
        # Dataframe untuk tingkat ini
        df_tingkat = info_df[info_df['Tingkat'] == tingkat][['Pemda', 'Klaster']].reset_index(drop=True)

        # Search box
        search_term = st.text_input(f"Cari {tingkat}...", key=f"search_{tingkat.lower()}")

        # Filter dataframe berdasarkan pencarian
        if search_term:
            df_display = df_tingkat[df_tingkat['Pemda'].str.contains(search_term, case=False)]
        else:
            df_display = df_tingkat
        
        # Tampilkan tabel
        st.dataframe(df_display, use_container_width=True, hide_index=True)


# --- KONTEN TAB 2: PROVINSI ---
with tab2:
    create_analysis_tab(
        "Provinsi", 
        info_df, 
        parameter_df, 
        kinerja_prov_df, 
        kondisi_prov_df, 
        stat_prov_df
    )

# --- KONTEN TAB 3: KABUPATEN/KOTA ---
with tab3:
    create_analysis_tab(
        "Kabupaten/Kota", 
        info_df, 
        parameter_df, 
        kinerja_kabkota_df, 
        kondisi_kabkota_df, 
        stat_kab_df
    )
