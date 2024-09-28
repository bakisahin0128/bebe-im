# indexer_backend.py

import os

from indexer_backend.src.embedder.PDFEmbedder import PDFEmbedder
from indexer_backend.src.embedder.embedder import Embedder
from indexer_backend.utils.indexer import Indexer
from indexer_backend.utils.openAI import OpenAIClient
from indexer_backend.utils.search import AISearcher


def main():
    # PDF'lerin bulunduğu dizini belirtin
    pdf_directory = "/home/baki/Masaüstü/bebeğim/indexer_backend/Bebeğim_pdf"  # PDF dosyalarının bulunduğu dizini buraya girin

    # OpenAIClient ve Embedder örneklerini oluşturuyoruz
    openai_client = OpenAIClient(engine="gpt-4o")  # GPT-4 motorunu kullanarak metin işleyeceğiz
    embedder = Embedder()

    # Azure Cognitive Search ile sayfaların indekslenip indekslenmediğini kontrol etmek için AISearcher kullanıyoruz
    ai_searcher = AISearcher()

    # Azure Cognitive Search'e her sayfayı anında indekslemek için Indexer kullanıyoruz
    indexer = Indexer([])  # Indexer başlatılır (boş listesi sadece başlatmak için)

    # PDFEmbedder sınıfı ile PDF'leri işleyip sayfa sayfa embedding yapacağız ve anında indeksleyeceğiz
    pdf_embedder = PDFEmbedder(pdf_directory, openai_client, embedder, ai_searcher, indexer)

    # PDF'lerin sayfa bazında işlenmesi ve her sayfanın anında indekslenmesi
    pdf_embedder.process_pdf_and_embed_by_page()

    print("Tüm PDF sayfaları işlendi ve indekslendi!")

if __name__ == "__main__":
    main()

