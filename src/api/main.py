from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import admin, auth, chat, documents, invoices, upload

app = FastAPI(title="AI Document Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(documents.router)


@app.get("/health")
def health():
    return {"status": "ok"}
