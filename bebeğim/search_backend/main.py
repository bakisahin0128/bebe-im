# search_backend.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from src.embedder.embedder import Embedder
from utils.openAI import OpenAIClient
from utils.search import AISearcher
from fastapi.middleware.cors import CORSMiddleware
from utils.system_messages import SYSTEM_MESSAGES_PDF

app = FastAPI()

# CORS Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit frontend'inizin adresi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    question: str


class SearchResult(BaseModel):
    pdf_name: str
    page_number: int
    content: str
    similarity_score: float


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


# Bileşenlerin Başlatılması
openai_client = OpenAIClient(engine="gpt-4o")  # GPT-4 motoru kullanılıyor
embedder = Embedder()
ai_searcher = AISearcher()


def embed_question(question_text: str) -> list:
    question_embedding = embedder.embed_text(question_text)
    return question_embedding


@app.post("/search", response_model=List[SearchResult])
def search(query: Query):
    try:
        question_embedding = embed_question(query.question)
        search_results = ai_searcher.search_similar_pdf_pages(question_embedding, top_k=10)
        if not search_results:
            raise HTTPException(status_code=404, detail="Herhangi bir sonuç bulunamadı.")
        return search_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat(chat_request: ChatRequest):
    try:
        # Soru embed'leniyor
        question_embedding = embed_question(chat_request.question)

        # En yakın 5 sonucu arıyoruz
        search_results = ai_searcher.search_similar_pdf_pages(question_embedding, top_k=10)

        if not search_results:
            raise HTTPException(status_code=404, detail="Herhangi bir sonuç bulunamadı.")

        # Arama sonuçlarını bir araya getiriyoruz
        context = "\n\n".join([
            f"PDF: {result['pdf_name']} - Sayfa {result['page_number']}\n{result['content']}"
            for result in search_results
        ])


        user_message = f"Soru: {chat_request.question}\n\nBelgeler:\n{context}"

        # GPT-4'ten cevap alıyoruz
        answer = openai_client.generate_response(SYSTEM_MESSAGES_PDF, user_message)

        return ChatResponse(answer=answer)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
