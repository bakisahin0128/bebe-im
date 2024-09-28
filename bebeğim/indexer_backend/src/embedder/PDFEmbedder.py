import os
from indexer_backend import config
from indexer_backend.src.embedder.embedder import Embedder
import PyPDF2
from tqdm import tqdm  # tqdm kütüphanesi ilerleme çubuğu için eklendi


class PDFEmbedder:
    """
    A class to process PDFs, extract content from each page, and generate embeddings page by page.
    It stores each page's embedding and content in a simple dictionary format, and indexes each page
    after it is processed.
    """

    def __init__(self, pdf_directory, openai_client, embedder, ai_searcher, indexer):
        """
        Initializes the PDFEmbedder with the directory containing PDFs, an instance of OpenAIClient, and an Embedder.

        Args:
            pdf_directory (str): Path to the directory where PDFs are stored.
            openai_client (OpenAIClient): Instance of the OpenAIClient for text extraction and cleaning.
            embedder (Embedder): Instance of the Embedder for generating text embeddings.
            ai_searcher (AISearcher): Instance of the AISearcher to check if a page is already indexed.
            indexer (Indexer): Instance of the Indexer to index each processed page.
        """
        self.pdf_directory = pdf_directory
        self.openai_client = openai_client
        self.embedder = embedder
        self.ai_searcher = ai_searcher
        self.indexer = indexer

    def get_total_page_count(self):
        """
        Computes the total number of pages across all PDFs in the directory.

        Returns:
            int: Total number of pages.
        """
        total_pages = 0
        for pdf_file in os.listdir(self.pdf_directory):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_directory, pdf_file)
                try:
                    with open(pdf_path, 'rb') as pdf_file_obj:
                        reader = PyPDF2.PdfReader(pdf_file_obj)
                        total_pages += len(reader.pages)
                except Exception as e:
                    pass  # Hata durumunda log bırakmıyoruz
        return total_pages

    def is_page_already_indexed(self, pdf_name, page_number):
        """
        Checks if the given page of a PDF is already indexed in Azure Cognitive Search.

        Args:
            pdf_name (str): The name of the PDF file.
            page_number (int): The page number to check.

        Returns:
            bool: True if the page is already indexed, False otherwise.
        """
        # Azure Cognitive Search'te o PDF sayfasının zaten indekslenip indekslenmediğini kontrol et
        return self.ai_searcher.is_page_indexed(pdf_name, page_number)

    def process_pdf_and_embed_by_page(self):
        """
        Processes all PDFs in the directory, extracts and cleans the content of each page,
        checks if it's already indexed, generates embeddings, and indexes the page immediately.

        Returns:
            list: A list of dictionaries where each dictionary contains pdf_name, page_number, content, and embedding.
        """
        total_pages = self.get_total_page_count()  # Toplam sayfa sayısını hesapla

        # tqdm ilerleme çubuğu başlatılıyor
        progress_bar = tqdm(total=total_pages, desc="Processing PDFs", unit="page")

        for pdf_file in os.listdir(self.pdf_directory):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_directory, pdf_file)
                raw_text_by_page = self.extract_text_by_page(pdf_path)

                # Her sayfa için işlem yapılıyor
                for page_number, raw_text in raw_text_by_page.items():
                    if raw_text:
                        # Sayfa zaten indekslenmişse atla
                        if self.is_page_already_indexed(pdf_file, page_number):
                            progress_bar.update(1)  # İlerleme çubuğunu güncelle
                            continue

                        # Sayfa indekslenmemişse işlem yap
                        cleaned_text = self.openai_client.extract_text_using_gpt(raw_text)
                        embedding = self.embedder.embed_text(cleaned_text)

                        if embedding:
                            # Sayfayı indeksle
                            document = {
                                "pdf_name": pdf_file,
                                "page_number": page_number,
                                "content": cleaned_text,
                                "embedding": embedding
                            }
                            self.indexer.ingest_document(document)  # Her sayfayı direkt indeksle

                    # İlerleme çubuğunda bir sayfa işlemi tamamlandığında ilerleme kaydediliyor
                    progress_bar.update(1)

        progress_bar.close()  # İlerleme çubuğunu kapat

    def extract_text_by_page(self, pdf_path):
        """
        Extracts raw text from each page of a PDF file using PyPDF2.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            dict: A dictionary where keys are page numbers and values are the extracted raw text from that page.
        """
        try:
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text_by_page = {}
                for page_num in range(len(reader.pages)):
                    text_by_page[page_num + 1] = reader.pages[page_num].extract_text()  # Sayfa numarası 1'den başlıyor
                return text_by_page
        except Exception as e:
            return {}
