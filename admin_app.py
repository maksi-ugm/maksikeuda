import streamlit as st
import pandas as pd
from github import Github
import io

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
    st.info("Edit tabel di bawah seperti di Google Sheets. Klik 'Update Database' untuk menyimpan perubahan ke GitHub.")

    # Ambil konfigurasi dari Secrets
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "data.xlsx"

    try:
        # Baca data langsung dari GitHub agar selalu terbaru
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(FILE_PATH)
        df = pd.read_excel(io.BytesIO(contents.decoded_content), engine='openpyxl')

        # Google Sheets Style Editor
        edited_df = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            key="data_editor_key"
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
                mime="application/vnd.ms-excel"
            )

        with col2:
            # Fitur Restore/Update ke GitHub
            if st.button("🚀 Update & Restore Database"):
                with st.spinner("Sedang mengunggah perubahan ke GitHub..."):
                    # Konversi DataFrame ke Bytes
                    output = io.BytesIO()
                    edited_df.to_excel(output, index=False, engine='openpyxl')
                    new_content = output.getvalue()
                    
                    # Update file di GitHub
                    repo.update_file(
                        path=contents.path,
                        message="Admin Update Database via Streamlit Editor",
                        content=new_content,
                        sha=contents.sha
                    )
                    st.success("✅ Database berhasil diperbarui! App utama akan terupdate otomatis dalam beberapa saat.")
                    st.balloons()

    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
