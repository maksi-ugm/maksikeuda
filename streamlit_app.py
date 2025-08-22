import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import base64
from pathlib import Path

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
        tren_df = pd.read_excel(xls, "TREN")
        
        kinerja_kabkota_df = pd.concat([kinerja_kab_df, kondisi_kab_df], ignore_index=True)
        kondisi_kabkota_df = pd.concat([kondisi_kab_df, kinerja_kab_df], ignore_index=True)

        return (info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, 
                kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df, tren_df)

    except Exception as e:
        st.error(f"Terjadi error fatal saat memuat data: {e}. Pastikan file 'data.xlsx' dan semua sheet di dalamnya (INFO, PARAMETER, TREN, dll.) sudah benar.")
        return (None,) * 9

# --- MEMUAT DATA DI AWAL ---
data_tuple = load_data_from_excel()

# --- FUNGSI GRAFIK ---
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
            fig.add_trace(go.Scatter(x=stat_filtered['TAHUN'], y=stat_filtered['MEDIAN'], mode='lines', line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'), name='Profil Pemda Setara', hoverinfo='x+y'))

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
    
    st.markdown("---")
    st.markdown("### Analisis Tren 3 Tahun Terakhir")

    if not selected_pemda:
        st.write("Pilih pemerintah daerah untuk melihat analisis tren.")
        return

    for pemda in selected_pemda:
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
            st.markdown(f"- Analisis tren untuk **{pemda}** pada indikator ini tidak tersedia.")


# --- FUNGSI UNTUK MEMBUAT TAB ANALISIS ---
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
            
        color_palette = st.selectbox("Pilih Palet Warna", ['Default', 'G10', 'T10', 'Pastel', 'Dark2'], key=f'color_{level.lower()}')
        chart_type = st.radio("Pilih Tipe Grafik", ('Garis', 'Batang', 'Area'), key=f'chart_{level.lower()}', horizontal=True)
        pilihan_data = st.radio("Pilih Tema Analisis", ('Kinerja Keuangan', 'Kondisi Keuangan'), key=f'data_type_{level.lower()}', horizontal=True)
        
        daftar_indikator = parameter_df[parameter_df['JENIS'] == pilihan_data]['INDIKATOR'].unique()
        if pilihan_data == 'Kondisi': main_df = kondisi_df
        else: main_df = kinerja_df

        selected_indikator = st.selectbox("Pilih Indikator", daftar_indikator, key=f'indikator_{level.lower()}')
        
        daftar_klaster = sorted(info_level_df['KLASTER'].dropna().unique())
        if not daftar_klaster:
            st.warning(f"Tidak ada klaster untuk tingkat {pilihan_tingkat}.")
            selected_klaster = None
        else:
            selected_klaster = st.selectbox("Pilih Klaster", daftar_klaster, key=f'klaster_{level.lower()}')
        
        if selected_klaster:
            daftar_pemda = sorted(info_level_df[info_level_df['KLASTER'] == selected_klaster]['PEMDA'].dropna().unique())
            multiselect_label = f"Pilih {pilihan_tingkat if level == 'Kabupaten/Kota' else 'Provinsi'}"
            selected_pemda = st.multiselect(multiselect_label, daftar_pemda, key=f'pemda_{level.lower()}')
        else:
            selected_pemda = []

    with chart_col:
        if selected_indikator and selected_klaster is not None:
            display_chart(selected_pemda, selected_indikator, selected_klaster, main_df, stat_df, chart_type, color_palette, pilihan_tingkat, tren_df)
            
            st.markdown("---")
            st.markdown(f"### Deskripsi Indikator: {selected_indikator}")
            
            deskripsi_row = parameter_df.loc[parameter_df['INDIKATOR'] == selected_indikator]
            if not deskripsi_row.empty:
                def escape_md(text):
                    if isinstance(text, str):
                        return text.replace('_', '\\_')
                    return text

                definisi = escape_md(deskripsi_row['DEFINISI'].iloc[0])
                harapan = escape_md(deskripsi_row['NILAI_HARAPAN'].iloc[0])
                rumus = escape_md(deskripsi_row['RUMUS'].iloc[0])

                if pd.notna(definisi) and definisi:
                    st.markdown("**Definisi**")
                    st.info(f"{definisi}")
                
                if pd.notna(harapan) and harapan:
                    st.markdown("**Nilai Harapan**")
                    st.info(f"{harapan}")

                if pd.notna(rumus) and rumus:
                    st.markdown("**Rumus**")
                    st.info(f"`{rumus}`")
            else:
                st.warning("Informasi deskripsi untuk indikator ini tidak tersedia.")
        else:
            st.info(f"Silakan lengkapi semua filter di kolom kiri untuk menampilkan data.")

# --- STRUKTUR UTAMA APLIKASI ---

# --- HEADER ---

# 1. Fungsi untuk mengubah gambar menjadi format yang bisa dibaca HTML
def img_to_base64(img_path_str):
    img_path = Path(img_path_str)
    if not img_path.is_file():
        return None
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 2. Siapkan path logo dan encode ke Base64
logo_base64 = img_to_base64("header.png")

# 3. Tampilkan header menggunakan HTML dan CSS kustom jika logo ditemukan
if logo_base64:
    st.markdown(f"""
    <style>
        /* Menargetkan container utama Streamlit untuk menghilangkan padding atas */
        div.block-container:first-of-type {{
            padding: 1rem 1rem 0rem !important; /* Atur: atas | kanan-kiri | bawah */
        }}
        /* Membuat wadah header dengan layout flexbox */
        .custom-header {{
            display: flex;
            align-items: center;
            gap: 12px; /* UBAH INI: untuk mengatur jarak antara logo dan teks */
            margin-bottom: 20px; /* Jarak header ke judul dashboard di bawahnya */
        }}
        /* Menghilangkan margin bawaan dari judul teks */
        .custom-header h2, .custom-header h4 {{
            margin: 0;
            padding: 0;
            font-weight: 500; /* Atur ketebalan font */
        }}
    </style>
    
    <div class="custom-header">
        <img src="data:image/jpeg;base64,{logo_base64}" width="100">
        <div>
            <h4>Program Studi Magister Akuntansi</h4>
            <h2>Fakultas Ekonomika dan Bisnis</h2>
            <h4>Universitas Gadjah Mada</h4>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Pesan jika file logo tidak ditemukan
    st.error("File 'header.png' tidak ditemukan. Pastikan file berada di folder yang sama dengan script.")

# --- AKHIR Header ---


st.title("📊 Dashboard Indeks Maksikeuda")

st.markdown("""
Dashboard interaktif ini dirancang untuk membantu Anda menganalisis data keuangan pemerintah daerah. Anda dapat:
- **Memilih** pemerintah daerah (Provinsi, Kabupaten, atau Kota).
- **Melihat** tren indikator kinerja & kondisi keuangannya dari tahun ke tahun.
- **Membandingkan** capaiannya dengan pemerintah daerah lain dalam satu klaster.
- **Mendapatkan** analisis tren otomatis dan deskripsi mendalam untuk setiap indikator.
- Database dashboard ini disusun berdasarkan data LKPD yang telah diaudit oleh BPK RI.
""")

if data_tuple is None or data_tuple[0] is None:
    st.stop()

info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df, tren_df = data_tuple

tab1, tab2, tab3 = st.tabs(["#### **Informasi**", "#### **Provinsi**", "#### **Kabupaten/Kota**"])

with tab1:
    st.header("Informasi Klaster Pemerintah Daerah")
    st.markdown("Gunakan kotak pencarian untuk menemukan pemerintah daerah di dalam setiap klaster.")
    col1, col2, col3 = st.columns(3, gap="large")
    for i, tingkat in enumerate(['Provinsi', 'Kabupaten', 'Kota']):
        with [col1, col2, col3][i]:
            st.subheader(f"Klaster {tingkat}")
            df_tingkat = info_df[info_df['TINGKAT'] == tingkat][['PEMDA', 'KLASTER']].reset_index(drop=True)
            label_pencarian = f"Cari {tingkat}..."
            search_term = st.text_input(label_pencarian, key=f"search_{tingkat}")
            if search_term: df_display = df_tingkat[df_tingkat['PEMDA'].str.contains(search_term, case=False)]
            else: df_display = df_tingkat
            st.dataframe(df_display, use_container_width=True, hide_index=True)

with tab2:
    create_analysis_tab("Provinsi", info_df, parameter_df, kinerja_prov_df, kondisi_prov_df, stat_prov_df, tren_df)

with tab3:
    create_analysis_tab("Kabupaten/Kota", info_df, parameter_df, kinerja_kabkota_df, kondisi_kabkota_df, stat_kab_df, tren_df)

# --- FOOTER CUSTOM ---
st.markdown("---")
st.markdown("Dibuat oleh **Mahasiswa Konsentrasi Akuntansi Sektor Publik, Magister Akuntansi FEB UGM**")
