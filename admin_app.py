import streamlit as st
import pandas as pd
from github import Github
import io
import requests

# --- 1. CONFIG & ULTRA-SLIM UI ---
st.set_page_config(page_title="Editor", layout="wide")

# CSS "Nuklir" untuk menghapus semua whitespace dan double scroll
st.markdown("""
    <style>
    /* 1. Hapus padding utama dan banner Streamlit di atas */
    header {visibility: hidden;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* 2. Matikan scroll halaman utama agar tidak ada double scroll */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
    }

    /* 3. Pastikan tombol radio (sheet) tidak makan tempat banyak */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }

    /* 4. Perkecil spasi antar elemen */
    [data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
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
    # --- HEADER MINIMALIS ---
    c_title, c_logout = st.columns([0.88, 0.12])
    with c_title:
        st.write("### 📊 Admin Panel")
    with c_logout:
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- KONEKSI DATA ---
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
            res = requests.get(contents.download_url, headers=headers)
            st.session_state.all_sheets = pd.read_excel(io.BytesIO(res.content), sheet_name=None, engine='openpyxl')

        # --- TABEL SELECTOR (RADIO) ---
        sh_list = list(st.session_state.all_sheets.keys())
        # Taruh radio di satu baris agar hemat tempat
        selected_sheet = st.radio("Pilih Sheet:", sh_list, horizontal=True, label_visibility="collapsed")
        
        # --- DATA EDITOR (FULL HEIGHT) ---
        # Tinggi disesuaikan agar pas di layar tanpa memicu scroll global
        # 75vh artinya 75% dari tinggi layar
        edited_df = st.data_editor(
            st.session_state.all_sheets[selected_sheet],
            num_rows="dynamic",
            use_container_width=True,
            height=500, 
            key=f"ed_{selected_sheet}"
        )
        st.session_state.all_sheets[selected_sheet] = edited_df

        # --- AKSI ---
        st.write("") # Spasi tipis
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
