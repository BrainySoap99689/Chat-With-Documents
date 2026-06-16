from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# Lazy DB connection: create on first use so imports don't fail when DB is down
conn = None

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def get_conn():
    global conn
    if conn is not None:
        return conn

    host = os.getenv("DB_HOST", "localhost")
    database = os.getenv("DB_NAME", "app_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "904689Pt")

    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
    )

    return conn

app = FastAPI()

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_HOST")],
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
    embedding = model.encode(chunk)
    return embedding.tolist()

def storeEmbeddings(chunks, document_name):
    conn_local = get_conn()
    for chunk in chunks:
        cursor = conn_local.cursor()
        embedding = createEmbeddings(chunk['chunk'])

        cursor.execute(
            """
            INSERT INTO document_chunks
            (
                document_name,
                page_number,
                chunk_text,
                embedding
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                document_name,
                chunk["page"],
                chunk["chunk"],
                embedding
            )
        )
        conn_local.commit()

def processPDF(pdf_path):
    pages = extract_text(pdf_path)
    chunks = chunkPages(pages)
    storeEmbeddings(chunks, pdf_path)

    return len(chunks)
    


@app.get("/changedRoute")
def home():
    return {"message": "Woah this is cool!"}