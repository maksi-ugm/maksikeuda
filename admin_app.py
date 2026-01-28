import streamlit as st
import pandas as pd
from github import Github
import io
import requests

# --- 1. KONFIGURASI HALAMAN & CSS ---
st.set_page_config(page_title="Admin Database", layout="wide")

# CSS Kustom untuk memaksa Scrollbar lebih besar dan terlihat
st.markdown("""
    <style>
    /* Mempertebal Scrollbar Global */
    ::-webkit-scrollbar {
        width: 15px;
        height: 15px;
    }
    ::-webkit-scrollbar-thumb {
        background: #888; 
        border-radius: 10px;
        border: 3px solid #f1f1f1;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555; 
    }
    
    /* Memaksa area data editor agar lebih luas */
    .stDataEditor div {
        overflow: visible !important;
    }
    
    /* Tombol Logout di pojok kanan atas */
    .logout-btn {
        float: right;
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
    # Header & Tombol Logout
    col_head, col_logout = st.columns([0.9, 0.1])
    with col_head:
        st.title("📊 Database Editor")
    with col_logout:
        if st.button("Logout"):
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
        
        # Load data awal
        if st.session_state.all_sheets is None:
            contents = repo.get_contents(FILE_PATH)
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(contents.download_url, headers=headers)
            st.session_state.all_sheets = pd.read_excel(io.BytesIO(response.content), sheet_name=None, engine='openpyxl')

        # --- NAVIGASI SHEET (PINDAH KE TENGAH) ---
        sheet_list = list(st.session_state.all_sheets.keys())
        st.write("### Pilih Tab Database:")
        selected_sheet = st.radio("Daftar Sheet:", sheet_list, horizontal=True)
        
        st.divider()

        # --- PENGATURAN KOLOM & DESIMAL ---
        current_df = st.session_state.all_sheets[selected_sheet]
        
        # Deteksi kolom angka
        num_cols = current_df.select_dtypes(include=['number']).columns
        
        # Konfigurasi: Kita gunakan format Indonesia (Koma)
        # Catatan: Tampilan di layar akan menyesuaikan Locale Browser Anda.
        # Jika browser Anda bahasa Indonesia, titik akan otomatis jadi koma.
        config = {col: st.column_config.NumberColumn(format="%.2f") for col in num_cols}

        # --- DATA EDITOR (SCROLLBAR BESAR) ---
        edited_df = st.data_editor(
            current_df,
            num_rows="dynamic",
            use_container_width=True,
            height=650, 
            key=f"editor_{selected_sheet}",
            column_config=config
        )

        # Simpan perubahan sementara ke session state
        st.session_state.all_sheets[selected_sheet] = edited_df

        # --- TOMBOL AKSI ---
        st.divider()
        c1, c2 = st.columns([1, 4])
        
        with c1:
            # Backup
            output_backup = io.BytesIO()
            with pd.ExcelWriter(output_backup, engine='openpyxl') as writer:
                for s_name, df in st.session_state.all_sheets.items():
                    df.to_excel(writer, sheet_name=s_name, index=False)
            
            st.download_button(
                label="📥 Download Backup",
                data=output_backup.getvalue(),
                file_name=f"backup_{FILE_PATH}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with c2:
            if st.button("🚀 Simpan Perubahan ke GitHub"):
                with st.status("Proses Sinkronisasi...", expanded=False) as status:
                    # AMBIL SHA TERBARU (Penting agar update kedua tidak error)
                    latest_contents = repo.get_contents(FILE_PATH)
                    
                    output_save = io.BytesIO()
                    with pd.ExcelWriter(output_save, engine='openpyxl') as writer:
                        for s_name, df in st.session_state.all_sheets.items():
                            df.to_excel(writer, sheet_name=s_name, index=False)
                    
                    repo.update_file(
                        path=latest_contents.path,
                        message="Admin Manual Update via Web Editor",
                        content=output_save.getvalue(),
                        sha=latest_contents.sha
                    )
                    status.update(label="✅ Berhasil Disimpan!", state="complete")
                    st.toast("Database Cloud diperbarui!", icon="✅")

    except Exception as e:
        st.error(f"Error: {e}")
