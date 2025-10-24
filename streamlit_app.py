import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import base64
from pathlib import Path

# --- KONFIGURASI HALAMAN (DI LUAR LOGIN) ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard Keuangan Pemda",
    page_icon="📊"
)

# --- BLOK KODE UNTUK AUTENTIKASI ---
def check_login():
    """Fungsi untuk menampilkan form login dan validasi."""
    
    # 1. Cek apakah 'logged_in' sudah ada di session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # 2. Ambil daftar user dari st.secrets
    try:
        users_db = st.secrets['credentials']['users']
    except (KeyError, FileNotFoundError):
        st.error("Error: Konfigurasi 'secrets' untuk kredensial user belum diatur oleh admin.")
        return False

    # 3. Jika user belum login, tampilkan form
    if not st.session_state.logged_in:
        st.title("Login Dasbor")
        st.sidebar.info("Silakan masukkan username dan password untuk mengakses dasbor.")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                # 4. Validasi kredensial
                if username in users_db and users_db[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username # Simpan username untuk sapaan
                    st.experimental_rerun()  # Muat ulang aplikasi setelah login berhasil
                else:
                    st.error("Username atau Password salah.")
        
        return False  # Hentikan eksekusi sisa skrip
    
    # 5. Jika sudah login, izinkan lanjut dan tampilkan tombol logout
    st.sidebar.success(f"Login sebagai: {st.session_state.get('username', 'User')}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.pop('username', None) # Hapus username dari state
        st.experimental_rerun() # Muat ulang untuk kembali ke form login
        
    return True # Izinkan eksekusi sisa skrip

# --- FUNGSI MEMUAT DATA ---
@st.cache_data
def load_data_from_excel(path="data.xlsx"):
    try:
        xls = pd.ExcelFile(path)
        info_df = pd.read_excel(xls, "INFO")
        parameter_df = pd.read_excel(xls, "PARAMETER")
        indikator_df = pd.read_excel(xls, "INDIKATOR")
        median_df = pd.read_excel(xls, "MEDIAN")
        tren_df = pd.read_excel(xls, "TREN")
        
        dataframes_to_clean = {
            'info': (info_df, ['PEMDA', 'KLASTER', 'TINGKAT']),
            'parameter': (parameter_df, ['INDIKATOR', 'JENIS']),
            'indikator': (indikator_df, ['INDIKATOR', 'PEMDA']),
            'median': (median_df, ['INDIKATOR', 'TINGKAT', 'KLASTER']),
            'tren': (tren_df, ['INDIKATOR', 'PEMDA'])
        }

        for df, columns in dataframes_to_clean.values():
            for col in columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()

        return info_df, parameter_df, indikator_df, median_df, tren_df

    except Exception as e:
        st.error(f"Terjadi error fatal saat memuat data: {e}. Pastikan file 'data.xlsx' dan semua sheet di dalamnya (INFO, PARAMETER, INDIKATOR, MEDIAN, TREN) sudah benar.")
        return (None,) * 5

# --- FUNGSI-FUNGSI TAMPILAN ---

def display_main_header():
    """Menampilkan header utama dengan perataan judul dan logo UGM yang presisi."""
    def img_to_base64(img_path_str):
        img_path = Path(img_path_str)
        if not img_path.is_file(): return None
        with open(img_path, "rb") as f: return base64.b64encode(f.read()).decode()

    logo_base64 = img_to_base64("header.png")
    
    st.markdown(f"""
    <style>
        /* Hide Streamlit elements */
        div[data-testid="stToolbar"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"], #MainMenu, footer, header {{visibility: hidden;}}
        
        /* Main Header Container */
        .header-container {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0rem;
        }}
        .main-title h1 {{
            margin: 0;
            padding: 0;
            font-size: 2.2em;
        }}
        .ugm-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            text-align: right;
        }}
        .ugm-text h4, .ugm-text h3 {{
            margin: 0;
            padding: 0;
            font-weight: 500;
            line-height: 1.2;
        }}
        .ugm-text h4 {{ font-size: 0.9em; }}
        .ugm-text h3 {{ font-size: 1.1em; }}
        
        /* Smaller font for customization header */
        .customization-header {{
            font-size: 0.9em;
            font-weight: bold;
            color: #555;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }}
    </style>

    <div class="header-container">
        <div class="main-title">
            <h1>📊 Dashboard Indeks Maksikeuda</h1>
        </div>
        <div class="ugm-header">
            <div class="ugm-text">
                <h4>Program Studi Magister Akuntansi</h4>
                <h3>Fakultas Ekonomika dan Bisnis</h3>
                <h4>Universitas Gadjah Mada</h4>
            </div>
            <img src="data:image/jpeg;base64,{logo_base64}" width="80">
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_intro():
    """Menampilkan teks pengantar dalam expander."""
    with st.expander("Informasi & Detail Dashboard"):
        st.markdown("""
        Dashboard interaktif ini dirancang untuk membantu Anda menganalisis data keuangan pemerintah daerah. Anda dapat:
        - **Memilih** pemerintah daerah (Provinsi, Kabupaten, atau Kota).
        - **Melihat** tren indikator kinerja & kondisi keuangannya dari tahun ke tahun.
        - **Membandingkan** capaiannya dengan pemerintah daerah lain dalam satu klaster.
        - **Mendapatkan** analisis tren otomatis dan deskripsi mendalam untuk setiap indikator.
        - Database dashboard ini disusun berdasarkan data LKPD yang telah diaudit oleh BPK RI.
        """)

def display_cluster_info_in_sidebar(df, tingkat):
    """Menampilkan tabel informasi klaster dalam expander di kolom filter."""
    with st.expander(f"🔎 Informasi Klaster {tingkat}"):
        search_term = st.text_input(f"Cari {tingkat}...", key=f"search_{tingkat}")
        df_tingkat = df[df['TINGKAT'] == tingkat][['PEMDA', 'KLASTER']].reset_index(drop=True)
        if search_term:
            df_display = df_tingkat[df_tingkat['PEMDA'].str.contains(search_term, case=False)]
        else:
            df_display = df_tingkat
        
        # KOREKSI: Mengatur indeks agar dimulai dari 1
        df_display.index = range(1, len(df_display) + 1)
        st.dataframe(df_display, use_container_width=True, height=300)

def display_chart(selected_pemda, selected_indikator, selected_klaster, indikator_df, median_df, chart_type, color_palette, tingkat_filter, tren_df):
    """Menampilkan grafik utama dan analisisnya."""
    if not selected_pemda:
        st.warning("Silakan pilih minimal satu pemerintah daerah untuk menampilkan grafik.")
        return

    fig = go.Figure()
    colors = px.colors.qualitative.Plotly if color_palette == 'Default' else getattr(px.colors.qualitative, color_palette)
    
    median_filtered = median_df[(median_df['KLASTER'] == selected_klaster) & (median_df['INDIKATOR'] == selected_indikator) & (median_df['TINGKAT'] == tingkat_filter)]
    
    if not median_filtered.empty:
        median_filtered = median_filtered.sort_values('TAHUN')
        fig.add_trace(go.Scatter(x=median_filtered['TAHUN'], y=median_filtered['MEDIAN'], mode='lines', line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'), name='Profil Pemda Setara', hoverinfo='x+y'))

    annotations_to_add = []
    for i, pemda in enumerate(selected_pemda):
        pemda_df = indikator_df[(indikator_df['PEMDA'] == pemda) & (indikator_df['INDIKATOR'] == selected_indikator)].copy()
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
    
    with st.expander("Analisis Tren 3 Tahun Terakhir"):
        if not selected_pemda:
            st.write("Pilih pemerintah daerah untuk melihat analisis tren.")
        else:
            for pemda in selected_pemda:
                tren_data = tren_df[(tren_df['INDIKATOR'] == selected_indikator) & (tren_df['PEMDA'] == pemda)]
                if not tren_data.empty:
                    nilai_tren = tren_data['NILAI'].iloc[0]
                    if nilai_tren.lower() == 'hijau': st.success(f"**Baik (Favorable)**: Indikator **{selected_indikator}** pada **{pemda}** menunjukkan tren **kenaikan**.")
                    elif nilai_tren.lower() == 'kuning': st.warning(f"**Tidak Pasti (Uncertain)**: Indikator **{selected_indikator}** pada **{pemda}** menunjukkan tren **fluktuasi**.")
                    elif nilai_tren.lower() == 'merah': st.error(f"**Tidak Baik (Unfavorable)**: Indikator **{selected_indikator}** pada **{pemda}** menunjukkan tren **penurunan**.")
                else:
                    st.markdown(f"- Analisis tren untuk **{pemda}** pada indikator ini tidak tersedia.")
    
    with st.expander(f"Deskripsi Indikator: {selected_indikator}"):
        deskripsi_row = parameter_df.loc[parameter_df['INDIKATOR'] == selected_indikator]
        if not deskripsi_row.empty:
            def escape_md(text):
                return str(text).replace('_', '\\_') if isinstance(text, str) else text
            
            definisi = escape_md(deskripsi_row['DEFINISI'].iloc[0])
            harapan = escape_md(deskripsi_row['NILAI_HARAPAN'].iloc[0])
            rumus = escape_md(deskripsi_row['RUMUS'].iloc[0])

            if pd.notna(definisi) and definisi: st.info(f"**Definisi**: {definisi}")
            if pd.notna(harapan) and harapan: st.info(f"**Nilai Harapan**: {harapan}")
            if pd.notna(rumus) and rumus: st.info(f"**Rumus**: `{rumus}`")
        else:
            st.warning("Informasi deskripsi untuk indikator ini tidak tersedia.")

# --- STRUKTUR UTAMA APLIKASI (DIBUNGKUS OLEH LOGIN) ---

# Panggil fungsi login. 
# Jika mengembalikan True (login berhasil), jalankan seluruh aplikasi.
if check_login():
    
    # Semua kode aplikasi asli Anda dimulai dari sini,
    # dan semuanya harus di-indentasi (menjorok ke dalam)
    
    display_main_header()
    display_intro()

    data_tuple = load_data_from_excel()
    if data_tuple[0] is None:
        st.stop()
    info_df, parameter_df, indikator_df, median_df, tren_df = data_tuple

    filter_col, chart_col = st.columns([2, 5])

    with filter_col:
        pilihan_tingkat = st.radio("Pilih Tingkat Pemerintah Daerah", ('Provinsi', 'Kabupaten', 'Kota'), horizontal=True)
        
        pilihan_data = st.radio("Pilih Tema Analisis", ('Kinerja Keuangan', 'Kondisi Keuangan'), horizontal=True)
        
        daftar_indikator = parameter_df[parameter_df['JENIS'] == pilihan_data]['INDIKATOR'].unique()
        selected_indikator = st.selectbox("Pilih Indikator", daftar_indikator)
        
        info_level_df = info_df[info_df['TINGKAT'] == pilihan_tingkat]
        
        # KOREKSI: Mengambil daftar klaster dan mengurutkannya secara numerik
        unique_klaster = info_level_df['KLASTER'].dropna().unique()
        try:
            # Coba urutkan sebagai angka jika memungkinkan
            daftar_klaster = sorted(unique_klaster, key=int)
        except ValueError:
            # Jika ada klaster non-numerik, urutkan sebagai teks biasa
            daftar_klaster = sorted(unique_klaster)
        
        if not daftar_klaster:
            st.warning(f"Tidak ada data klaster untuk tingkat {pilihan_tingkat}.")
            selected_klaster = None
            selected_pemda = []
        else:
            selected_klaster = st.selectbox("Pilih Klaster", daftar_klaster)
            
            pemda_in_klaster = sorted(info_level_df[info_level_df['KLASTER'] == selected_klaster]['PEMDA'].dropna().unique())
            selected_pemda = st.multiselect(f"Pilih {pilihan_tingkat}", pemda_in_klaster, placeholder="Pilih satu atau lebih")

        display_cluster_info_in_sidebar(info_df, pilihan_tingkat)
        
        st.markdown('<p class="customization-header">Kustomisasi Tampilan</p>', unsafe_allow_html=True)
        chart_type = st.radio("Pilih Tipe Grafik", ('Garis', 'Batang', 'Area'), horizontal=True)
        color_palette = st.selectbox("Pilih Palet Warna", ['Default', 'G10', 'T10', 'Pastel', 'Dark2'])

    with chart_col:
        if selected_indikator and selected_klaster is not None:
            display_chart(selected_pemda, selected_indikator, selected_klaster, indikator_df, median_df, chart_type, color_palette, pilihan_tingkat, tren_df)
        else:
            st.info("ℹ️ Silakan lengkapi semua filter di kolom kiri untuk menampilkan data analisis.")

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        Hak Cipta © 2025 Tim Pengembang MAKSI FEB UGM. Dilindungi Undang-Undang.<br>
        <a href="https://hakcipta.dgip.go.id/legal/c/Zjg5NzI5NDkyYTQxZDk1OGNlNjY0MWVjMDNjZGFmNzE=" target="_blank">Lihat Sertifikat HKI</a>
    </div>
    """, unsafe_allow_html=True)
