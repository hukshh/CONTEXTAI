from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload, chat, search, files, status
import os

app = FastAPI(title="ContextAI API")

# CORS: FRONTEND_URL is set as an env var on Render (your Vercel production URL).
# Localhost is always allowed for local development.
frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

# Build allowed origins list
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(status.router, prefix="/api", tags=["status"])


@app.get("/")
async def root():
    return {"message": "Welcome to ContextAI API"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    print(f"Starting uvicorn on 0.0.0.0:{port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
