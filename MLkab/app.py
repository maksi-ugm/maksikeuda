import streamlit as st
import pandas as pd
import joblib

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Prediksi Opini Publik",
    page_icon="📊",
    layout="centered"
)

# --- Muat Model yang Sudah Dilatih ---
# Pastikan file model ada di path yang benar
try:
    model = joblib.load('model_logistik.pkl')
except FileNotFoundError:
    st.error("File model 'model_logistik.pkl' tidak ditemukan. Pastikan file sudah di-upload ke repository GitHub.")
    st.stop() # Menghentikan eksekusi jika model tidak ada

# --- Antarmuka Aplikasi ---
st.title('📊 Aplikasi Prediksi Opini')
st.write("""
Aplikasi ini menggunakan model Machine Learning (Regresi Logistik) untuk memprediksi opini berdasarkan 11 indikator yang Anda masukkan.
""")

st.header('Masukkan Nilai Indikator:')

# Membuat input form
with st.form("prediction_form"):
    # Membuat 11 input slider untuk setiap indikator
    # Asumsi nama kolom adalah Indikator_1, Indikator_2, dst.
    # Ganti 'label' dan 'key' jika nama indikator Anda berbeda.
    indikator_inputs = {}
    for i in range(1, 12):
        # Anda bisa mengganti rentang nilai (0, 10) sesuai skala data Anda
        indikator_inputs[f'Indikator_{i}'] = st.slider(
            label=f'Nilai Indikator {i}', 
            min_value=0, 
            max_value=10, 
            value=5, # Nilai default
            key=f'indikator_{i}'
        )

    # Tombol untuk submit
    submit_button = st.form_submit_button(label='🔮 Lakukan Prediksi')


# --- Logika Prediksi ---
if submit_button:
    # Mengubah input dictionary menjadi DataFrame agar sesuai format training
    input_df = pd.DataFrame([indikator_inputs])
    
    st.write("---")
    st.subheader("Data Input Anda:")
    st.dataframe(input_df)

    # Melakukan prediksi
    prediction = model.predict(input_df)
    prediction_proba = model.predict_proba(input_df)

    # Menampilkan hasil
    st.subheader('Hasil Prediksi:')
    
    opini_hasil = prediction[0]
    
    if opini_hasil == 1: # Asumsi 1 = Opini WTP
        st.success(f'**Prediksi Opini: WTP**')
    else: # Asumsi 0 = Opini Negatif/Tidak Setuju
        st.error(f'**Prediksi Opini: TIDAK WTP**')
    
    st.write("Probabilitas Hasil:")
    st.write(f"Peluang Tidak WTP: **{prediction_proba[0][0]:.2f}**")
    st.write(f"Peluang WTP: **{prediction_proba[0][1]:.2f}**")


st.sidebar.info("Aplikasi ini dibuat untuk mendemonstrasikan model Regresi Logistik.")
