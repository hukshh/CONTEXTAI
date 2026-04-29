from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload, chat, search, files
import os

app = FastAPI(title="ContextAI API")

# Configure CORS
origins = [
    os.getenv("FRONTEND_URL", "*")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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
