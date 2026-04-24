📧 MailLens – AI Powered Gmail Intelligence Platform

An advanced full-stack AI application that transforms your Gmail inbox into a smart, searchable, and insightful system using LLMs, semantic search, and analytics.

🚀 Live Demo

🔗 https://mail-scraper-two.vercel.app

✨ Features
🔐 Authentication
Google OAuth 2.0 login
Secure token handling (access + refresh tokens)
Backend-controlled authentication flow
📬 Gmail Integration
Read-only access to Gmail
Fetch emails, threads, labels, metadata
Background sync & auto-backfill
🔍 Smart Search (Hybrid AI Search)
Keyword + Semantic search (pgvector)
Context-aware results using LLM (Groq)
Fast responses with Redis caching
📊 Analytics Dashboard
Email volume trends
Sender insights
Label distribution
Thread depth visualization
🧠 AI Analysis Studio
Ask questions in natural language
Converts queries → SQL via LLM
Generates dynamic charts (Recharts)
⚡ Background Processing
Smart sync (recent emails first)
Historical backfill (chunk-based)
Automated scheduling
🏗️ System Architecture
<img width="1536" height="1024" alt="ChatGPT Image Apr 24, 2026, 09_37_02 AM" src="https://github.com/user-attachments/assets/43c86e88-af26-4a94-a0c4-a82d66316f07" />


Frontend → Backend API → Database / Cache / AI / Gmail API

Frontend (React + Vite) → UI, charts, interactions
Backend (FastAPI) → API logic, OAuth, orchestration
Database (Supabase PostgreSQL + pgvector) → Emails & embeddings
Cache (Upstash Redis) → Faster queries
AI (Groq + Transformers) → NLP + semantic search
External API (Gmail API) → Email ingestion
🛠️ Tech Stack
Frontend
React 18
TypeScript
Vite
Zustand (state management)
TanStack Query
Recharts
Backend
FastAPI (Python 3.11)
Celery (background workers)
APScheduler (cron jobs)
Database & Cache
Supabase PostgreSQL
pgvector (embeddings)
Upstash Redis
AI & ML
Groq API (LLaMA models)
sentence-transformers (MiniLM)
External APIs
Google OAuth 2.0
Gmail API
Deployment
Frontend → Vercel
Backend → Hugging Face Spaces (Docker)
⚙️ Installation (Local Setup)
1. Clone Repository
git clone https://github.com/moukthika-23/Mail-Scraper.git
cd Mail-Scraper
2. Backend Setup
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
3. Frontend Setup
cd frontend
npm install
npm run dev
🔑 Environment Variables
Backend (.env)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

SUPABASE_URL=
SUPABASE_SERVICE_KEY=

REDIS_URL=
GROQ_API_KEY=
FRONTEND_URL=http://localhost:5173
Frontend (.env)
VITE_API_URL=http://localhost:8000/api/v1
🔄 Key Workflows
1. User Login & Sync
User clicks "Continue with Google"
Backend handles OAuth
Gmail access granted
Celery starts email sync
Emails stored + embeddings generated
2. Smart Search
User enters query
Query embedding generated
pgvector similarity search
Results + context sent to Groq LLM
AI-generated response returned
3. AI Analysis
User asks natural language query
Groq converts → SQL
Backend executes query
Data → charts (Recharts)
🐳 Docker (Backend)
docker build -t mail-scraper .
docker run -p 8000:8000 mail-scraper
☸️ Deployment
Backend (Hugging Face)
Create Docker Space
Add secrets (.env values)
Deploy
Frontend (Vercel)
Import repo
Set root → /frontend

Add env:

VITE_API_URL=https://your-backend-url/api/v1
📌 Key Highlights
🔍 Hybrid AI Search (keyword + semantic)
🧠 LLM-powered query engine
⚡ High performance with Redis caching
🔄 Background sync architecture
☁️ Fully cloud deployed system
👩‍💻 Author

Moukthika
📧 AI & Full Stack Developer
