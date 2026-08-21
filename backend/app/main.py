from fastapi import FastAPI
from app.core.database import engine, Base
from app.models.user import User


Base.metadata.create_all(bind=engine)

app=FastAPI(
    title="DocuMind AI",
    description="AI-Powered Business Assistent",
    version="1.0"
)

@app.get("/")
def root():
    return{"message":"DocuMind AI API is running"}

