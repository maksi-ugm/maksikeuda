import streamlit as st
import pandas as pd
from github import Github
import io
import requests

# --- 1. CONFIG & SLIM UI ---
st.set_page_config(page_title="Editor", layout="wide")

# CSS untuk membuang padding berlebih di atas (Minim Space)
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    div[data-testid="stForm"] {
        padding: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

def check_password():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.title("🔐 Login")
        user = st.text_input("User")
        pw = st.text_input("Pass", type="password")
        if st.button("Masuk"):
            if user == st.secrets["ADMIN_USER"] and pw == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Salah!")
        return False
    return True

if check_password():
    # --- HEADER KECIL (TITLE & LOGOUT) ---
    col_t, col_l = st.columns([0.85, 0.15])
    with col_t:
        st.markdown("### 📊 Database Admin") # Judul kecil (h3)
    with col_l:
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # --- KONEKSI GITHUB ---
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "data.xlsx"

    if "all_sheets" not in st.session_state:
        st.session_state.all_sheets = None

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        if st.session_state.all_sheets is None:
            contents = repo.get_contents(FILE_PATH)
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(contents.download_url, headers=headers)
            st.session_state.all_sheets = pd.read_excel(io.BytesIO(response.content), sheet_name=None, engine='openpyxl')

        # --- SHEET SELECTOR (TAB STYLE) ---
        sheet_list = list(st.session_state.all_sheets.keys())
        selected_sheet = st.radio("Pilih Tabel:", sheet_list, horizontal=True)
        
        # --- DATA EDITOR (PLAIN & SINGLE SCROLL) ---
        # Menghapus column_config agar format angka kembali ke asal
        edited_df = st.data_editor(
            st.session_state.all_sheets[selected_sheet],
            num_rows="dynamic",
            use_container_width=True,
            height=550, # Kunci tinggi agar scrollbar hanya muncul di dalam tabel
            key=f"editor_{selected_sheet}"
        )

        st.session_state.all_sheets[selected_sheet] = edited_df

        # --- ACTION BUTTONS ---
        st.write("")
        c1, c2 = st.columns([0.2, 0.8])
        
        with c1:
            # Backup
            out_b = io.BytesIO()
            with pd.ExcelWriter(out_b, engine='openpyxl') as writer:
                for s_name, df in st.session_state.all_sheets.items():
                    df.to_excel(writer, sheet_name=s_name, index=False)
            
            st.download_button("📥 Backup", out_b.getvalue(), f"data_backup.xlsx", "application/vnd.ms-excel")

        with c2:
            if st.button("🚀 SIMPAN KE CLOUD", use_container_width=True):
                with st.spinner("Proses simpan..."):
                    # SHA terbaru wajib diambil agar tidak conflict
                    latest = repo.get_contents(FILE_PATH)
                    out_s = io.BytesIO()
                    with pd.ExcelWriter(out_s, engine='openpyxl') as writer:
                        for s_name, df in st.session_state.all_sheets.items():
                            df.to_excel(writer, sheet_name=s_name, index=False)
                    
                    repo.update_file(latest.path, "Update data", out_s.getvalue(), latest.sha)
                    st.toast("Data Berhasil Disimpan!", icon="✅")

    except Exception as e:
        st.error(f"Error: {e}")
