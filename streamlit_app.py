import streamlit as st
import pandas as pd
import plotly.express as px

# HARUS PALING ATAS
st.set_page_config(layout="wide", page_title="Dashboard Pemda")

# Load data
@st.cache_data
def load_data():
    xls = pd.ExcelFile("data.xlsx")
    rasio_df = pd.read_excel(xls, "rasio")
    interpretasi_df = pd.read_excel(xls, "interpretasi")

    def load_sheet(sheet):
        return pd.read_excel(xls, sheet).rename(columns={
            "Tahun": "tahun", "Pemda": "pemda", "Kluster": "kluster",
            "Indikator": "indikator", "Nilai": "nilai"
        })

    keu_prov = load_sheet("keu_prov")
    kin_prov = load_sheet("kin_prov")
    keu_kab = load_sheet("keu_kab")
    kin_kab = load_sheet("kin_kab")

    return rasio_df, interpretasi_df, keu_prov, kin_prov, keu_kab, kin_kab

rasio_df, interpretasi_df, keu_prov_df, kin_prov_df, keu_kab_df, kin_kab_df = load_data()

# Plot helper pakai Plotly
def plotly_chart(df, title, chart_type):
    if df.empty:
        st.warning("Data kosong, silakan pilih Pemda & Indikator.")
        return

    # Tambah kolom label gabungan: "Pemda (Kluster X)"
    df = df.copy()
    df["label"] = df["pemda"] + " (Kluster " + df["kluster"].astype(str) + ")"

    if chart_type == "Garis":
        fig = px.line(df, x="tahun", y="nilai", color="label", markers=True)
    elif chart_type == "Batang":
        fig = px.bar(df, x="tahun", y="nilai", color="label", barmode="group")
    elif chart_type == "Area":
        fig = px.area(df, x="tahun", y="nilai", color="label")
    else:
        st.error("Tipe chart tidak dikenali.")
        return

    fig.update_layout(title=title, xaxis_title="Tahun", yaxis_title="Nilai", legend_title="Pemda", height=500)
    st.plotly_chart(fig, use_container_width=True)

# Sidebar filter inside tabs
def tab_content(sheet_df, rasio_df, tab_title, key_prefix):
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Filter Data")

        pemda_options = sorted(sheet_df["pemda"].unique())
        selected_pemda = st.multiselect("Pilih Pemda (Bisa lebih dari 1)", pemda_options, key=f"{key_prefix}_pemda")

        indikator_options = sorted(sheet_df["indikator"].unique())
        selected_indikator = st.selectbox("Pilih Indikator", indikator_options, key=f"{key_prefix}_indikator")

        chart_type = st.selectbox("Jenis Grafik", ["Garis", "Batang", "Area"], key=f"{key_prefix}_chart")

        deskripsi = rasio_df.loc[rasio_df["rasio"] == selected_indikator, "penjelasan"]
        st.markdown("### Deskripsi Indikator")
        st.info(deskripsi.values[0] if not deskripsi.empty else "-")

    with col2:
        if selected_pemda and selected_indikator:
            filtered_df = sheet_df[
                (sheet_df["pemda"].isin(selected_pemda)) &
                (sheet_df["indikator"] == selected_indikator)
            ]
            plotly_chart(filtered_df, f"{tab_title} - {selected_indikator}", chart_type)

            # Interpretasi box kosong (tanpa error)
            st.markdown("### Interpretasi")
            st.markdown(
                """
                <div style='border:1px solid #ddd; border-radius:8px; padding:10px; min-height:100px; background-color:#f9f9f9;'>
                <!-- Nanti isi interpretasi di sini -->
                </div>
                """,
                unsafe_allow_html=True
            )

# App layout
st.title("Dashboard Kinerja & Keuangan Pemda")

tabs = st.tabs(["Keuangan Provinsi", "Kinerja Provinsi", "Keuangan Kab/Kota", "Kinerja Kab/Kota"])

with tabs[0]:
    tab_content(keu_prov_df, rasio_df, "Keuangan Provinsi", "keu_prov")

with tabs[1]:
    tab_content(kin_prov_df, rasio_df, "Kinerja Provinsi", "kin_prov")

with tabs[2]:
    tab_content(keu_kab_df, rasio_df, "Keuangan Kab/Kota", "keu_kab")

with tabs[3]:
    tab_content(kin_kab_df, rasio_df, "Kinerja Kab/Kota", "kin_kab")
