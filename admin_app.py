import streamlit as st
import pandas as pd
from github import Github
import io
import base64

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
        # Koneksi ke GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(FILE_PATH)
        
        # PERBAIKAN: Manual decoding base64 untuk menghindari error 'unsupported encoding'
        file_data = base64.b64decode(contents.content)
        df = pd.read_excel(io.BytesIO(file_data), engine='openpyxl')

        # Google Sheets Style Editor
        # Kita beri key agar state editor terjaga
        edited_df = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_utama"
        )

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            # Fitur Backup Lokal
            towrite = io.BytesIO()
            edited_df.to_excel(towrite, index=False, engine='openpyxl')
            st.download_button(
                label="📥 Download Backup (Excel)",
                data=towrite.getvalue(),
                file_name=f"backup_{FILE_PATH}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

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
