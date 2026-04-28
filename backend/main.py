from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import upload, chat

app = FastAPI(title="ContextAI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Welcome to ContextAI API"}
