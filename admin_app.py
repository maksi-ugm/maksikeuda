import streamlit as st
import pandas as pd
from github import Github
import io
import requests

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="Database Editor", layout="wide")

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
    st.title("📊 Database Editor (Multi-Sheet)")
    
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "data.xlsx"

    # Inisialisasi session state untuk menyimpan data agar tidak hilang saat pindah sheet
    if "all_sheets" not in st.session_state:
        st.session_state.all_sheets = None

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(FILE_PATH)
        
        # Ambil data mentah jika belum ada di session state
        if st.session_state.all_sheets is None:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(contents.download_url, headers=headers)
            # sheet_name=None artinya membaca SEMUA sheet sekaligus menjadi Dictionary
            st.session_state.all_sheets = pd.read_excel(io.BytesIO(response.content), sheet_name=None, engine='openpyxl')

        # --- Navigasi Sheet ---
        sheet_list = list(st.session_state.all_sheets.keys())
        selected_sheet = st.selectbox("Pilih Sheet yang ingin diedit:", sheet_list)

        st.write(f"Editing Sheet: **{selected_sheet}**")
        
        # --- Editor Data ---
        # Height ditambahkan agar scroll bar lebih besar/nyaman
        edited_df = st.data_editor(
            st.session_state.all_sheets[selected_sheet],
            num_rows="dynamic",
            use_container_width=True,
            height=600, 
            key=f"editor_{selected_sheet}"
        )

        # Simpan perubahan sementara ke session state
        st.session_state.all_sheets[selected_sheet] = edited_df

        st.divider()
        
        # Definisikan kolom sebelum digunakan agar tidak error 'not defined'
        col1, col2 = st.columns(2)

        with col1:
            # Generate Excel untuk Backup (Semua Sheet)
            towrite = io.BytesIO()
            with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
                for sheet_name, df in st.session_state.all_sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            st.download_button(
                label="📥 Download Backup (Semua Sheet)",
                data=towrite.getvalue(),
                file_name=f"backup_full_{FILE_PATH}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col2:
            if st.button("🚀 Update & Restore Database ke GitHub"):
                with st.spinner("Sedang memproses seluruh sheet..."):
                    # Simpan semua sheet dari session_state ke satu file Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for sheet_name, df in st.session_state.all_sheets.items():
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    new_content = output.getvalue()
                    
                    repo.update_file(
                        path=contents.path,
                        message="Admin Update All Sheets via Streamlit",
                        content=new_content,
                        sha=contents.sha
                    )
                    st.success("✅ Semua Sheet berhasil diperbarui di GitHub!")
                    # Reset session state agar data terbaru ditarik ulang nanti
                    st.session_state.all_sheets = None 
                    st.balloons()

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.all_sheets = None
        st.rerun()
