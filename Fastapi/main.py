from fastapi import FastAPI
from routers import documents

app = FastAPI()

# Include the documents router
app.include_router(documents.router, prefix="/api")

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Multimodal Research Assistant API"}
