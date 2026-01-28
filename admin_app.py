import streamlit as st
import pandas as pd
from github import Github
import io
import requests

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Admin Database", layout="wide")

# CSS Kustom untuk memperbesar tampilan dan mempertegas scrollbar
st.markdown("""
    <style>
    .stDataFrame {
        border: 1px solid #e6e9ef;
        border-radius: 5px;
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
    st.title("📊 Database Editor")
    
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "data.xlsx"

    # Inisialisasi session state
    if "all_sheets" not in st.session_state:
        st.session_state.all_sheets = None

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Load data jika kosong
        if st.session_state.all_sheets is None:
            contents = repo.get_contents(FILE_PATH)
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(contents.download_url, headers=headers)
            st.session_state.all_sheets = pd.read_excel(io.BytesIO(response.content), sheet_name=None, engine='openpyxl')
            st.session_state.current_sha = contents.sha

        # --- Navigasi Sheet ---
        sheet_list = list(st.session_state.all_sheets.keys())
        selected_sheet = st.sidebar.selectbox("📂 Pilih Sheet:", sheet_list)
        
        st.subheader(f"Sheet: {selected_sheet}")

        # Konfigurasi Kolom (Otomatis deteksi angka untuk format Indonesia)
        current_df = st.session_state.all_sheets[selected_sheet]
        num_cols = current_df.select_dtypes(include=['number']).columns
        
        # Mapping format desimal (Koma untuk Indonesia)
        col_config = {col: st.column_config.NumberColumn(format="%.2f") for col in num_cols}

        # --- Editor Data ---
        # Height ditambah ke 700 agar scrollbar lebih manusiawi
        edited_df = st.data_editor(
            current_df,
            num_rows="dynamic",
            use_container_width=True,
            height=700, 
            key=f"editor_{selected_sheet}",
            column_config=col_config
        )

        # Simpan perubahan sementara ke session state
        st.session_state.all_sheets[selected_sheet] = edited_df

        # --- Floating Action Buttons (Sticky-like) ---
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            # Generate Excel untuk Backup
            towrite = io.BytesIO()
            with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
                for sheet_name, df in st.session_state.all_sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            st.download_button(
                label="📥 Download Backup",
                data=towrite.getvalue(),
                file_name=f"backup_full_{FILE_PATH}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download file saat ini ke komputer Anda"
            )

        with col2:
            if st.button("🚀 Simpan ke GitHub", help="Klik untuk memperbarui database di Cloud"):
                with st.status("Menyimpan ke GitHub...", expanded=False) as status:
                    try:
                        # 1. Tarik SHA terbaru tepat sebelum update (Mencegah error update beruntun)
                        current_contents = repo.get_contents(FILE_PATH)
                        
                        # 2. Convert Data
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            for sheet_name, df in st.session_state.all_sheets.items():
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # 3. Push ke GitHub
                        repo.update_file(
                            path=current_contents.path,
                            message="Admin Update via Streamlit Data Editor",
                            content=output.getvalue(),
                            sha=current_contents.sha
                        )
                        
                        status.update(label="✅ Tersimpan!", state="complete")
                        st.toast("Perubahan berhasil disimpan ke GitHub!", icon="🚀")
                        
                    except Exception as e:
                        st.error(f"Gagal simpan: {e}")

    except Exception as e:
        st.error(f"Kesalahan Koneksi: {e}")

    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
