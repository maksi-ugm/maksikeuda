import streamlit as st
import pandas as pd
from github import Github
import io
import requests

# --- 1. CONFIG & ULTRA-SLIM UI ---
st.set_page_config(page_title="Editor", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
    }
    [data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

def check_password():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.title("🔐 Login")
        user = st.text_input("User")
        pw = st.text_input("Pass", type="password")
        if st.button("Masuk"):
            if user == st.secrets["ADMIN_USER"] and pw == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Salah!")
        return False
    return True

if check_password():
    # --- HEADER ---
    c_title, c_logout = st.columns([0.88, 0.12])
    with c_title: st.write("### 📊 Admin Panel")
    with c_logout:
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- KONEKSI DATA ---
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "data.xlsx"

    if "all_sheets" not in st.session_state: st.session_state.all_sheets = None

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        if st.session_state.all_sheets is None:
            contents = repo.get_contents(FILE_PATH)
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            res = requests.get(contents.download_url, headers=headers)
            st.session_state.all_sheets = pd.read_excel(io.BytesIO(res.content), sheet_name=None, engine='openpyxl')

        # --- TABEL SELECTOR ---
        sh_list = list(st.session_state.all_sheets.keys())
        selected_sheet = st.radio("Sheet:", sh_list, horizontal=True, label_visibility="collapsed")
        
        # --- DATA FILTER LOGIC ---
        df_original = st.session_state.all_sheets[selected_sheet]
        
        # Baris Filter (Search & Dropdown)
        f1, f2, f3 = st.columns([0.4, 0.3, 0.3])
        
        with f1:
            search_query = st.text_input("🔍 Search data...", placeholder="Cari keyword apapun...", label_visibility="collapsed")
        with f2:
            # Otomatis deteksi kolom 'Tahun' jika ada
            tahun_list = ["Semua Tahun"] + sorted(df_original['Tahun'].unique().tolist()) if 'Tahun' in df_original.columns else ["Semua"]
            selected_tahun = st.selectbox("Tahun", tahun_list, label_visibility="collapsed")
        with f3:
            # Otomatis deteksi kolom 'Pemda' atau 'Nama Pemda' jika ada
            pemda_col = next((c for c in df_original.columns if 'Pemda' in c), None)
            pemda_list = ["Semua Pemda"] + sorted(df_original[pemda_col].unique().tolist()) if pemda_col else ["Semua"]
            selected_pemda = st.selectbox("Pemda", pemda_list, label_visibility="collapsed")

        # Proses Filtering
        df_filtered = df_original.copy()
        
        if search_query:
            # Search di semua kolom (convert ke string dulu)
            df_filtered = df_filtered[df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
        
        if selected_tahun != "Semua Tahun" and 'Tahun' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Tahun'] == selected_tahun]
            
        if selected_pemda != "Semua Pemda" and pemda_col:
            df_filtered = df_filtered[df_filtered[pemda_col] == selected_pemda]

        # --- DATA EDITOR ---
        # Penting: Jika memfilter, data_editor akan mengedit "view" saja. 
        # Untuk simpan permanen, kita harus update df_original menggunakan index.
        edited_df = st.data_editor(
            df_filtered,
            num_rows="dynamic",
            use_container_width=True,
            height=450, 
            key=f"ed_{selected_sheet}_{selected_tahun}_{selected_pemda}" # Key unik agar filter refresh bener
        )
        
        # Update Master Data (Update baris yang diedit berdasarkan index asli)
        st.session_state.all_sheets[selected_sheet].update(edited_df)

        # --- AKSI ---
        b1, b2 = st.columns([0.15, 0.85])
        with b1:
            out_b = io.BytesIO()
            with pd.ExcelWriter(out_b, engine='openpyxl') as writer:
                for s_name, df in st.session_state.all_sheets.items():
                    df.to_excel(writer, sheet_name=s_name, index=False)
            st.download_button("📥 Backup", out_b.getvalue(), "backup.xlsx", use_container_width=True)

        with b2:
            if st.button("🚀 SIMPAN PERUBAHAN KE CLOUD", use_container_width=True):
                with st.spinner("Saving..."):
                    latest = repo.get_contents(FILE_PATH)
                    out_s = io.BytesIO()
                    with pd.ExcelWriter(out_s, engine='openpyxl') as writer:
                        for s_name, df in st.session_state.all_sheets.items():
                            df.to_excel(writer, sheet_name=s_name, index=False)
                    repo.update_file(latest.path, "Update", out_s.getvalue(), latest.sha)
                    st.toast("Tersimpan!")

    except Exception as e:
        st.error(f"Error: {e}")
