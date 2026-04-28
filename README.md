# ContextAI

ContextAI is an AI-powered document assistant designed to help users interact with their PDF documents using a Retrieval-Augmented Generation (RAG) pipeline. This repository contains the foundation for a production-ready full-stack application.

## 🚀 Overview

ContextAI allows users to upload PDF documents and ask questions about their content through a clean, ChatGPT-style interface. While currently in Phase 1 (Foundation), the architecture is ready for RAG integration, embeddings, and vector database support.

## 🛠️ Tech Stack

- **Frontend**: [Next.js](https://nextjs.org/) (React)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Styling**: Vanilla CSS (Custom design system)
- **API**: OpenAI API (Planned for Phase 2)
- **Vector DB**: FAISS (Planned for Phase 2)

## ✨ Current Features

- **PDF Upload**: Multipart form-data support for local PDF storage.
- **SaaS UI**: Minimal, professional grey/white theme.
- **Chat Interface**: Responsive chat bubbles with "Thinking..." loading states.
- **Modular Architecture**: Clean separation between routes, services, and components.

## 📂 Project Structure

```text
Root/
├── frontend/           # Next.js Application
│   ├── components/     # Reusable UI components
│   ├── pages/          # Application routes
│   ├── services/       # API communication logic
│   └── styles/         # Global design system
├── backend/            # FastAPI Application
│   ├── routes/         # API endpoints (upload, chat)
│   ├── services/       # Business logic (placeholders)
│   ├── utils/          # Helper functions
│   └── main.py         # Entry point
└── uploads/            # Local storage for documents
```

## ⚙️ Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   python -m uvicorn main:app --reload
   ```
   The backend will be available at `http://localhost:8000`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:3000`.

## 🛡️ License

MIT License