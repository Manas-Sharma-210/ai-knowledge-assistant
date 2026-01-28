from fastapi import FastAPI
from app.routes.upload import router as upload_router

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Knowledge Assistant backend running"}
app.include_router(upload_router)
