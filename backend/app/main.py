from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import audit, auth, decisions, keywords, pdfs
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(decisions.router)
app.include_router(keywords.router)
app.include_router(pdfs.router)
app.include_router(audit.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
