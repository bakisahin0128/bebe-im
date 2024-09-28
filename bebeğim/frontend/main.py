# app.py

import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

# Çevresel değişkenleri yükleyin
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API URL'leri
SEARCH_API_URL = "http://localhost:8000/search"
CHAT_API_URL = "http://localhost:8000/chat"

# Sayfa ayarları
st.set_page_config(page_title="AI Search ve Chat Arayüzü", layout="wide")

# Özel CSS
st.markdown(
    """
    <style>
    .big-font {
        font-size:20px !important;
    }
    .highlight {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<p class="big-font">Balım için Özel tasarlanmış Chatbota Hoşgeldin!!</p>', unsafe_allow_html=True)

# Sidebar Ayarları
st.sidebar.title("Ayarlar")
theme = st.sidebar.selectbox("Tema Seçin", ["Işık", "Koyu"])
language = st.sidebar.selectbox("Dil Seçin", ["Türkçe", "İngilizce"])

st.sidebar.markdown("### Yardım")
st.sidebar.info("Bu uygulama hakkında daha fazla bilgi için [Buraya](#) tıklayın.")

# Sekmeler oluşturuyoruz
tab1, tab2, tab3 = st.tabs(["Chat", "Arama", "Doküman Yükleme"])

with tab2:
    st.header("AI Search")
    # Kullanıcıdan soru al
    question = st.text_area("Soru Sorun:", height=150, placeholder="Örneğin: Şirketinizin vizyonu nedir?",
                            help="Sorunuzu detaylı ve açık bir şekilde yazın.")

    if st.button("Ara"):
        if question.strip() == "":
            st.warning("Lütfen bir soru girin.")
        else:
            with st.spinner("Arama yapılıyor..."):
                try:
                    # FastAPI backend'ine POST isteği gönder
                    response = requests.post(SEARCH_API_URL, json={"question": question})

                    if response.status_code == 200:
                        results = response.json()
                        if results:
                            st.success("En Alakalı Sonuçlar:")
                            # Benzerlik Skoru Grafiği
                            df = pd.DataFrame(results)
                            fig, ax = plt.subplots(figsize=(10, 6))
                            ax.barh(df['pdf_name'] + " - Sayfa " + df['page_number'].astype(str),
                                    df['similarity_score'], color='skyblue')
                            ax.set_xlabel('Benzerlik Skoru')
                            ax.set_title('En Alakalı Sonuçların Benzerlik Skorları')
                            st.pyplot(fig)

                            # Sonuçları Listelerken Kart Görünümü
                            for idx, result in enumerate(results, start=1):
                                with st.container():
                                    col1, col2 = st.columns([1, 3])
                                    with col1:
                                        st.markdown(f"### {idx}. {result['pdf_name']} - Sayfa {result['page_number']}")
                                    with col2:
                                        st.write(result['content'])
                                        st.write(f"**Benzerlik Skoru:** {result['similarity_score']}")
                                    st.markdown("---")
                        else:
                            st.info("Herhangi bir sonuç bulunamadı.")
                    elif response.status_code == 404:
                        st.info("Herhangi bir sonuç bulunamadı.")
                    else:
                        st.error(f"Bir hata oluştu: {response.json().get('detail', 'Bilinmeyen hata')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"API ile bağlantı kurulurken hata oluştu: {e}")

with tab1:
    st.header("İstediğini sor bebeğim")
    # Kullanıcıdan soru al
    chat_question = st.text_area("Chatbot'a Sorunuz:", height=150, placeholder="Örneğin: Baki Beni ne kadar seviyor.",
                                 help="Sorunuzu detaylı ve açık bir şekilde yazın.")

    if st.button("Cevapla"):
        if chat_question.strip() == "":
            st.warning("Lütfen bir soru girin.")
        else:
            with st.spinner("Cevap oluşturuluyor..."):
                try:
                    # FastAPI backend'ine POST isteği gönder
                    response = requests.post(CHAT_API_URL, json={"question": chat_question})

                    if response.status_code == 200:
                        answer = response.json().get("answer", "")
                        st.success("Cevap:")
                        st.markdown(answer)  # Markdown formatında göster
                        # Geçmişi güncelle
                        if "history" not in st.session_state:
                            st.session_state.history = []
                        st.session_state.history.append({"question": chat_question, "answer": answer})

                        # Geri Bildirim Bölümü
                        feedback = st.radio("Cevap ne kadar yardımcı oldu?",
                                            ["Çok Yardımcı Oldu", "Yardıma İhtiyacım Var", "Yardımcı Olmadı"],
                                            key=len(st.session_state.history))
                        if st.button("Geri Bildirim Gönder", key=f"feedback_{len(st.session_state.history)}"):
                            st.success("Geri bildiriminiz alındı, teşekkür ederiz!")
                            # Geri bildirimi kaydedebilirsiniz (örneğin, bir veritabanına)
                    elif response.status_code == 404:
                        st.info("Herhangi bir sonuç bulunamadı.")
                    else:
                        st.error(f"Bir hata oluştu: {response.json().get('detail', 'Bilinmeyen hata')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"API ile bağlantı kurulurken hata oluştu: {e}")

    st.markdown("---")
    st.header("Sorgu Geçmişi")
    if "history" in st.session_state and st.session_state.history:
        for entry in st.session_state.history:
            st.markdown(f"**Soru:** {entry['question']}")
            st.markdown(f"**Cevap:** {entry['answer']}")
            st.markdown("---")
    else:
        st.info("Henüz herhangi bir sorgu yapmadınız.")

with tab3:
    st.header("Doküman Yükleme")
    uploaded_files = st.file_uploader("PDF dosyalarını yükleyin", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            bytes_data = uploaded_file.read()
            st.markdown(f"**Dosya Adı:** {uploaded_file.name}")
            st.markdown(f"**Dosya Boyutu:** {uploaded_file.size / 1024:.2f} KB")
            # Dosyayı backend'e göndererek işleyebilirsiniz
            # Örneğin, bir API endpoint'i oluşturup dosyayı gönderebilirsiniz
            # response = requests.post("http://localhost:8000/upload", files={"file": uploaded_file})
            # if response.status_code == 200:
            #     st.success("Dosya başarıyla yüklendi.")
            # else:
            #     st.error("Dosya yüklenirken hata oluştu.")
