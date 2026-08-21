from fastapi import FastAPI

app=FastAPI(
    title="DocuMind AI",
    description="AI-Powered Business Assistent",
    version="1.0"
)

@app.get("/")
def root():
    return{"message":"DocuMind AI API is running"}

