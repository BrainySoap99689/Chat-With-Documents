from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
import os

app = FastAPI()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)

    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        pages.append({
            "page": page_num + 1,
            "text": page.get_text()
        })

    return pages

def chunkPages(pages):
    chunks = []

    for page in pages:
        page_chunks = splitter.create_documents([page["text"]])
        for chunk in page_chunks:
            chunks.append({
                "page": page["page"],
                "chunk": chunk.page_content
            })

    return chunks

def createEmbeddings(chunk):
    response = client.embeddings.create(
        input=chunk,
        model="text-embedding-3-small"
    )

    return response.data[0].embedding


@app.get("/changedRoute")
def home():
    return {"message": "Woah this is cool!"}