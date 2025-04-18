# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import os
import google.generativeai as genai
import time
import re

URL_temperature = "https://industrial.ubidots.com/api/v1.6/devices/esp32/suhu/lv"
URL_humidity = "https://industrial.ubidots.com/api/v1.6/devices/esp32/kelembaban/lv"
URL_ultrasonik = "https://industrial.ubidots.com/api/v1.6/devices/esp32/ultrasonik/lv"
URL_ldr = "https://industrial.ubidots.com/api/v1.6/devices/esp32/ldr/lv"
headers = {"X-Auth-Token": "BBUS-1VLDcPJ8z9MPntKtXWcPlZJVVo4r7d"}
proses()

# ========== KONFIGURASI ==========
st.set_page_config(
    page_title="Geo DETEKSI by: The Explorer",
    layout="wide",
    page_icon="🏫"
)

# ========== GEMINI ENGINE ==========
class GeminiRecommendationEngine:
    def __init__(self):
        if 'GEMINI_API_KEY' not in st.secrets:
            st.error("API Key Gemini tidak ditemukan di secrets.toml")
            self.enabled = False
            return
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            available_models = [m.name for m in genai.list_models()]
            self.model_name = "models/gemini-1.5-pro-latest" if "models/gemini-1.5-pro-latest" in available_models else "models/gemini-pro"
            self.model = genai.GenerativeModel(self.model_name)
            self.enabled = True
        except Exception as e:
            st.error(f"Gagal inisialisasi Gemini: {str(e)}")
            self.enabled = False

    def generate_recommendations(self):
        proses()
        if not self.enabled:
            return ["⚠️ Sistem rekomendasi AI tidak aktif"]

        try:
            prompt = f"""
            Buat 3 rekomendasi spesifik dan singkat untuk menganalisis kondisi lingkungan terhadap kemungkinan terjadinya bencana tanah longsor berdasarkan data berikut: 
            - Suhu: {temperature_value} °C
            - Kelembaban: {humidity_value} %
            - Cahaya: {ldr_value} Lux
            - Ultrasonik: {ultrasonik_value} Cm
            Format markdown dengan heading dan bullet point.
            """
            response = self.model.generate_content(prompt)
            return self._parse_recommendations(response.text)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return ["⚠️ Tidak dapat menghasilkan rekomendasi"]

    def _parse_recommendations(self, text):
        parts = [s.strip() for s in text.split("###") if s.strip()]
        return parts[:3] if parts else ["⚠️ Tidak ada data yang bisa ditampilkan"]

# ========== DASHBOARD ==========
def proses():
    response_temperature = requests.get(URL_temperature,headers=headers)
    response_humidity = requests.get(URL_humidity,headers=headers)
    response_ultrasonik = requests.get(URL_ultrasonik,headers=headers)
    response_ldr = requests.get(URL_ldr,headers=headers)

    temperature_value = float(response_temperature.text)
    humidity_value = response_humidity.text
    ultrasonik_value = float(response_ultrasonik.text)
    ldr_value = response_ldr.text    

    st.session_state.temperature = temperature_value
    st.session_state.humidity = humidity_value   
    st.session_state.ultrasonik = ultrasonik_value  
    st.session_state.ldr = ldr_value
def main():
    st.title("🏫 Geo DETEKSI by: The Explorer")
    engine = GeminiRecommendationEngine()

    if "temperature" not in st.session_state:
        st.session_state.temperature = 0
    if "humidity" not in st.session_state:
        st.session_state.humidity = 0   
    if "ultrasonik" not in st.session_state:
        st.session_state.ultrasonik = 0
    if "ldr" not in st.session_state:
        st.session_state.ldr = 0
    if "llm" not in st.session_state:   
        st.session_state.llm = ""

    proses()       

    #st.markdown("Temperature: " + str(temperature_value))

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("🌡️ Sensor Suhu DHT11", f"{st.session_state.temperature} °C")
    col2.metric("💧 Kelembaban DHT11", f"{st.session_state.humidity} %")  
    col3.metric("📡 Sensor Ultrasonik", f"{st.session_state.ultrasonik} Cm")
    col4.metric("💡 Sensor LDR", f"{st.session_state.ldr} Lux")
    st.write(st.session_state.llm)  

    with st.sidebar:
        st.header("📊 Informasi Sensor")
        REFRESH_INTERVAL = st.slider("Interval Refresh (detik)", 5, 60, 15)
        st.markdown("### 🎯 Nilai Kondisi Normal")
        st.markdown("============================\n- 🌡️ Suhu: 22–26 °C\n- 💧 Kelembaban: 40–60 %\n- 📡 Ultrasonik: <45 Cm\n- 💡 Cahaya: 40–70 Lux" )

    st.markdown("## 🧠 Rekomendasi AI")

    if st.button("✨ Hasilkan Rekomendasi AI"):
        with st.spinner("Menganalisis Kondisi Lingkungan..."):
            st.session_state.recommendations = engine.generate_recommendations()
            st.session_state.show_recommendations = True

    if st.session_state.get("show_recommendations", False):
        with st.expander("📋 Lihat Rekomendasi Lengkap", expanded=True):
            for rec in st.session_state.get("recommendations", []):
                st.markdown(f"### {rec.splitlines()[0]}")
                for line in rec.splitlines()[1:]:
                    st.markdown(line)

    # Auto-refresh
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

# ========== RUN APLIKASI ==========
if __name__ == "__main__":
    main()
