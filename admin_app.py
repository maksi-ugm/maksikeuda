import streamlit as st
import pandas as pd
from github import Github
import io
import base64
import requests

# --- 1. FUNGSI LOGIN ---
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

# --- 2. MAIN APP ---
if check_password():
    st.set_page_config(page_title="Database Editor", layout="wide")
    st.title("📊 Database Editor (Admin Only)")
    st.info("Edit tabel di bawah. Klik 'Update Database' untuk menimpa file di GitHub.")

    # Ambil konfigurasi dari Secrets
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "data.xlsx"

    try:
        # 1. Inisialisasi GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(FILE_PATH)
        
        # 2. Ambil data mentah menggunakan URL download resmi dari GitHub
        # Cara ini lebih stabil untuk file biner (Excel)
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(contents.download_url, headers=headers)
        
        if response.status_code == 200:
            file_data = response.content
            # 3. Baca ke Pandas
            df = pd.read_excel(io.BytesIO(file_data), engine='openpyxl')
        else:
            st.error(f"Gagal mendownload file. Status code: {response.status_code}")
            st.stop()

        # --- Editor Data ---
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor_v2")
        with col2:
            # Fitur Update ke GitHub
            if st.button("🚀 Update & Restore Database"):
                with st.spinner("Sedang memproses..."):
                    # Konversi DataFrame yang sudah diedit ke Bytes
                    output = io.BytesIO()
                    edited_df.to_excel(output, index=False, engine='openpyxl')
                    new_content = output.getvalue()
                    
                    # Update file di GitHub
                    repo.update_file(
                        path=contents.path,
                        message="Admin Update via Streamlit Data Editor",
                        content=new_content,
                        sha=contents.sha
                    )
                    st.success("✅ Database berhasil diperbarui!")
                    st.balloons()

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
        st.info("Pastikan nama file di GitHub adalah 'data.xlsx' dan token memiliki akses yang benar.")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
