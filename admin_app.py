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
    html, body, [data-testid="stAppViewContainer"] { overflow: hidden !important; }
    [data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

def check_password():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.title("🔐 Login")
        u = st.text_input("User"); p = st.text_input("Pass", type="password")
        if st.button("Masuk"):
            if u == st.secrets["ADMIN_USER"] and p == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.logged_in = True; st.rerun()
            else: st.error("Salah!")
        return False
    return True

if check_password():
    # --- HEADER ---
    c_t, c_l = st.columns([0.88, 0.12])
    with c_t: st.write("### 📊 Admin Panel")
    with c_l:
        if st.button("🚪 Logout", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]; REPO_NAME = st.secrets["REPO_NAME"]; FILE_PATH = "data.xlsx"
    if "all_sheets" not in st.session_state: st.session_state.all_sheets = None

    try:
        g = Github(GITHUB_TOKEN); repo = g.get_repo(REPO_NAME)
        if st.session_state.all_sheets is None:
            contents = repo.get_contents(FILE_PATH)
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            res = requests.get(contents.download_url, headers=headers)
            st.session_state.all_sheets = pd.read_excel(io.BytesIO(res.content), sheet_name=None, engine='openpyxl')

        # --- TABEL SELECTOR ---
        sh_list = list(st.session_state.all_sheets.keys())
        selected_sheet = st.radio("Sheet:", sh_list, horizontal=True, label_visibility="collapsed")
        
        # --- DYNAMIC COLUMN FILTER ---
        df_master = st.session_state.all_sheets[selected_sheet]
        
        # Pilih kolom mana yang mau difilter
        cols_to_filter = st.multiselect("🔍 Pilih kolom untuk difilter/cari:", df_master.columns.tolist(), placeholder="Klik untuk cari per kolom...")
        
        df_filtered = df_master.copy()
        
        if cols_to_filter:
            # Buat kolom input secara dinamis sesuai jumlah kolom yang dipilih
            filter_cols = st.columns(len(cols_to_filter))
            for i, col_name in enumerate(cols_to_filter):
                with filter_cols[i]:
                    query = st.text_input(f"Cari di {col_name}", key=f"filter_{selected_sheet}_{col_name}", label_visibility="collapsed", placeholder=f"Filter {col_name}...")
                    if query:
                        # Filter Case Insensitive
                        df_filtered = df_filtered[df_filtered[col_name].astype(str).str.contains(query, case=False, na=False)]

        # --- DATA EDITOR ---
        # Key digabungkan dengan query agar editor refresh saat filter berubah
        edited_df = st.data_editor(
            df_filtered,
            num_rows="dynamic",
            use_container_width=True,
            height=430, 
            key=f"editor_{selected_sheet}_{len(df_filtered)}" 
        )
        
        # Sinkronisasi ke master data berdasarkan Index asli
        st.session_state.all_sheets[selected_sheet].update(edited_df)

        # --- AKSI ---
        st.write("")
        b1, b2 = st.columns([0.15, 0.85])
        with b1:
            out_b = io.BytesIO()
            with pd.ExcelWriter(out_b, engine='openpyxl') as writer:
                for s_name, df in st.session_state.all_sheets.items(): df.to_excel(writer, sheet_name=s_name, index=False)
            st.download_button("📥 Backup", out_b.getvalue(), "backup.xlsx", use_container_width=True)

        with b2:
            if st.button("🚀 SIMPAN PERUBAHAN KE CLOUD", use_container_width=True):
                with st.spinner("Saving..."):
                    latest = repo.get_contents(FILE_PATH)
                    out_s = io.BytesIO()
                    with pd.ExcelWriter(out_s, engine='openpyxl') as writer:
                        for s_name, df in st.session_state.all_sheets.items(): df.to_excel(writer, sheet_name=s_name, index=False)
                    repo.update_file(latest.path, "Update", out_s.getvalue(), latest.sha)
                    st.toast("Tersimpan!")

    except Exception as e:
        st.error(f"Error: {e}")
