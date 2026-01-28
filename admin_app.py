import streamlit as st
import pandas as pd
from github import Github
import io
import requests

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Admin Database", layout="wide")

# CSS AGRESIF: Memaksa scrollbar muncul dan besar
st.markdown("""
    <style>
    /* 1. Paksa Scrollbar Tabel agar Selalu Terlihat & Tebal */
    [data-testid="stDataFrame"] > div {
        overflow: auto !important;
    }
    
    /* Chrome, Edge, Safari */
    [data-testid="stDataFrame"] ::-webkit-scrollbar {
        width: 20px !important;    /* Lebar scrollbar vertikal */
        height: 20px !important;   /* Tinggi scrollbar horizontal */
        display: block !important;
    }

    [data-testid="stDataFrame"] ::-webkit-scrollbar-track {
        background: #f1f1f1 !important;
        border-radius: 10px;
    }

    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
        background: #c1c1c1 !important; /* Warna abu-abu yang jelas */
        border: 4px solid #f1f1f1 !important; /* Memberi jarak agar mudah dilihat */
        border-radius: 10px !important;
    }

    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8 !important; /* Lebih gelap saat disentuh */
    }

    /* 2. Style untuk Radio Button (Sheet Selector) agar lebih lega */
    div[data-testid="stWidgetLabel"] {
        font-weight: bold;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

def check_password():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.title("🔐 Admin Login")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == st.secrets["ADMIN_USER"] and pw == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Username atau Password salah")
        return False
    return True

if check_password():
    # Tombol Logout di paling atas
    if st.button("🚪 Logout", use_container_width=False):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

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

        # Navigasi Sheet
        sheet_list = list(st.session_state.all_sheets.keys())
        selected_sheet = st.radio("📑 Pilih Sheet / Tabel:", sheet_list, horizontal=True)
        
        st.write("---")

        # --- DATA EDITOR ---
        # Kami hapus column_config agar format angka kembali ke default (plain)
        # Kami kunci height di 600px agar scrollbar HARUS muncul
        edited_df = st.data_editor(
            st.session_state.all_sheets[selected_sheet],
            num_rows="dynamic",
            use_container_width=True,
            height=600, 
            key=f"editor_{selected_sheet}"
        )

        st.session_state.all_sheets[selected_sheet] = edited_df

        # --- TOMBOL AKSI ---
        st.write("")
        c1, c2 = st.columns([1, 4])
        
        with c1:
            # Backup All Sheets
            output_backup = io.BytesIO()
            with pd.ExcelWriter(output_backup, engine='openpyxl') as writer:
                for s_name, df in st.session_state.all_sheets.items():
                    df.to_excel(writer, sheet_name=s_name, index=False)
            
            st.download_button(
                label="📥 Download Backup",
                data=output_backup.getvalue(),
                file_name=f"backup_full.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with c2:
            if st.button("🚀 SIMPAN PERUBAHAN KE CLOUD", use_container_width=True):
                with st.status("Menghubungkan ke GitHub...") as status:
                    latest_contents = repo.get_contents(FILE_PATH)
                    output_save = io.BytesIO()
                    with pd.ExcelWriter(output_save, engine='openpyxl') as writer:
                        for s_name, df in st.session_state.all_sheets.items():
                            df.to_excel(writer, sheet_name=s_name, index=False)
                    
                    repo.update_file(
                        path=latest_contents.path,
                        message="Admin Update via Web Editor",
                        content=output_save.getvalue(),
                        sha=latest_contents.sha
                    )
                    status.update(label="✅ Berhasil Disimpan!", state="complete")
                    st.toast("Data sudah sinkron!")

    except Exception as e:
        st.error(f"Error: {e}")
