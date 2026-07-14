from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy DB connection: create on first use so imports don't fail when DB is down
conn = None

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def get_conn():
    host = os.getenv("DB_HOST")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    return psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
    )



splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

@app.get("/documents")
async def get_documents():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT document_name FROM document_names ORDER BY id DESC LIMIT 10;")
    documents = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return documents

def check_db(pdf_path):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT EXISTS ( 
            SELECT 1 FROM document_names WHERE document_name = %s
            
        )""",
        (pdf_path,)
    )
    ans = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return ans

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
    conn = get_conn()
    for chunk in chunks:
        cursor = conn.cursor()
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
        conn.commit()
    cursor.close()
    conn.close()
def trackDocuments(pdf_path):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO document_names
        (
            document_name
        )
        VALUES (%s)
        """,
        (pdf_path,)
    )
    conn.commit()
    cursor.close()
    conn.close()

def processPDF(pdf_path):
    pages = extract_text(pdf_path)
    chunks = chunkPages(pages)
    storeEmbeddings(chunks, pdf_path)
    trackDocuments(pdf_path)

    return len(chunks)
    
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # Save the uploaded file to a temporary location
    temp_file_path = f"temp_{file.filename}"
    check = check_db(temp_file_path)
    if check:
        return {"Error Message": f"{file.filename} has already been uploaded."}
    else:
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        # Process the PDF and store embeddings
        num_chunks = processPDF(file.filename)

        # Clean up the temporary file
        os.remove(temp_file_path)

        return {"message": f"Processed {num_chunks} chunks from {file.filename}"}