from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload, chat, search, files
import os

app = FastAPI(title="ContextAI API")

# Configure CORS safely
frontend_url = os.getenv("FRONTEND_URL", "*").strip()
if frontend_url.endswith("/"):
    frontend_url = frontend_url[:-1]

origins = [frontend_url]
# Fallback local origins just in case
if frontend_url != "*":
    origins.extend([
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://contextai-seven.vercel.app"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if frontend_url == "*" else origins,
    allow_credentials=False if frontend_url == "*" else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(files.router, prefix="/api", tags=["files"])

@app.get("/")
async def root():
    return {"message": "Welcome to ContextAI API"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    print(f"Starting uvicorn on 0.0.0.0:{port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
