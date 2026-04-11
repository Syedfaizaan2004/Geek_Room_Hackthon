DEMO LINK: https://ai-financial-agent-backend.onrender.com/

# AI Financial Agent

A comprehensive AI-powered financial research platform combining a FastAPI backend with a modern Next.js frontend. The platform serves as an advanced financial analyst, providing real-time market data, AI-generated investment insights, portfolio analysis, deterministic math models, and predictive modeling using vector search (Qdrant) and LangGraph.

---

## 🚀 Features

- **Deep Financial Research:** Full 8-engine analysis covering fundamentals, growth, risk, scenario testing, valuation, and peer comparisons.
- **AI-Powered Insights:** Automatically synthesize complex financial data into human-readable narratives using Gemini/LangChain.
- **Scenario Stress Testing:** Run deterministic macroeconomic scenarios (e.g., recession, inflation, rate hikes) to see the potential impact on stock price projections and risk metrics.
- **Market & Fundamental Data Integration:** Real-time data pulling capabilities combined with deeper deterministic logic and historical trending.
- **Semantic Memory (RAG):** Built-in Qdrant vector database storage allowing the AI to recall previous analyses, user preferences, and market history for personalized recommendations.
- **Modern Interactive UI:** A sleek Next.js React frontend built with TailwindCSS and Recharts, offering interactive visual charts (stock prices, profit/loss profiles) and dynamic data panels.
- **Comparison Engine:** Benchmark competitors and peers instantly to find market leaders.

---

## 🏗 Project Structure

This repository is organized as a monorepo containing two independent services:

- **`backend/`**: A fully-featured Python FastAPI application handling core business logic, database operations, external API data retrieval, ML embeddings, and the custom LangGraph AI agent pipeline.
- **`frontend/`**: A Next.js (React) web application utilizing TailwindCSS for styling, Recharts for data visualization, and Zustand for state management.

---

## 🛠 Tech Stack

### Frontend
- **Framework:** Next.js 16 / React 19
- **Styling:** TailwindCSS 4
- **State Management:** Zustand
- **Charting:** Recharts
- **Icons:** Lucide-React
- **Language:** TypeScript

### Backend
- **Framework:** FastAPI / Uvicorn (Async Web Server)
- **AI & Graph Logic:** LangChain / LangGraph, Langchain Google GenAI
- **Data & Math:** Pandas, NumPy, yfinance
- **Vector Database:** Qdrant
- **Classical DB:** SQLAlchemy / SQLite (Ready for asyncpg/Postgres)
- **Validation:** Pydantic

---

## 🔑 LLM Provider Setup & Environment Variables

The backend relies heavily on environment variables for LLM integration and system configuration.

1. Navigate to the `backend/` directory.
2. Create a `.env` file from the example (if available) or create a new one.
3. Configure your desired LLM Provider (Default: Google Gemini).

Example `.env` configuration:
```env
APP_ENV=development
DEBUG=True

# Core Application Settings (Required)
DATABASE_URL=sqlite+aiosqlite:///./financial_agent.db
SECRET_KEY=your_super_secret_key_here

# LLM Setup (Gemini is recommended)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Qdrant Vector DB Settings (Required for Semantic Memory)
QDRANT_URL=https://your-qdrant-cluster-url.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

> **Note:** Set `APP_ENV=production` for production deployments.

---

## 🛡️ Security

- **Environment Isolation:** The monorepo uses separate environments to prevent variable leakage. Secrets (like `GEMINI_API_KEY`) should only be exposed to the Backend service.
- **CORS:** Controlled via the FastAPI backend (`backend/app/main.py`). The default is permissive for development but must be updated for production to only allow the frontend URL.
- **Endpoints validation:** Strong HTTP level validation via Pydantic v2 schemas on incoming payload and query string parameters.
- **No Direct DB Access for Frontend:** The frontend interacts singularly with the REST APIs. Complete separation of concerns between client architecture and database internals.

---

## 📡 API Overview

The backend exposes a comprehensive set of REST endpoints grouped by analytical phases, usually grouped under `/api/v1/`:

- **`/api/v1/market`**: Basic price endpoints and current moving averages.
- **`/api/v1/fundamentals`**: Company financial health scores, profit margins, and liquidity parameters.
- **`/api/v1/risk`**: Quantitative safety scores, debt metrics, and volatility.
- **`/api/v1/forecast`**: Price bounds, standard deviations, and short/medium-term projections.
- **`/api/v1/scenario`**: Endpoints passing varying stress-test macros into deterministic valuation scripts.
- **`/api/v1/compare`**: Peer benchmarking based on combined factors (Risk, Fundamentals, Valuation).
- **`/api/v1/agent & /insights`**: Core AI endpoints that execute LangGraph chains to synthesize the raw endpoints above into narrative responses.

*(You can explore interactive API documentation dynamically by starting the backend and navigating to [http://localhost:8000/docs](http://localhost:8000/docs))*

---

## 💻 Local Development

### Prerequisites
- Node.js (v18+)
- Python 3.10+

### Backend Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the `.env` file as described in the *LLM Setup* section.
5. Run the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure the `.env.local` to point to the backend:
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
Open [http://localhost:3000](http://localhost:3000) to view the application in your browser.

---

## ☁️ Deployment

This project is configured to be deployed easily on any Docker-compatible platform (e.g., [Railway](https://railway.app/), [DigitalOcean App Platform](https://www.digitalocean.com/products/app-platform), AWS, or a self-hosted VPS) utilizing the included Dockerfiles and `docker-compose.yml`.

### Option 1: Docker Compose (Self-Hosted / VPS)
You can run the entire stack on a single server using Docker Compose:

1. Clone the repository on your server.
2. Create a `.env` file at the root of the project with your required variables:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./financial_agent.db
   SECRET_KEY=your_super_secret_key_here
   GEMINI_API_KEY=your_gemini_api_key
   QDRANT_URL=https://your-qdrant-cluster-url.cloud.qdrant.io
   QDRANT_API_KEY=your_qdrant_api_key
   # NEXT_PUBLIC_API_URL should point to the public domain where your backend is hosted
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   ```
3. Run the orchestration command:
   ```bash
   docker-compose up -d --build
   ```
4. The backend will be available on port `8000` and the frontend on port `3000`. We recommend putting a reverse proxy (like Nginx or Traefik) in front of them for SSL.

### Option 2: Platform as a Service (Railway, Render, etc.)
If you prefer deploying on a managed PaaS, you can deploy the `backend` and `frontend` folders as two separate services:

1. **Deploy the Backend:** 
   - Create a new **Web Service** on your platform.
   - Set the Root Directory to `/backend`.
   - The platform will automatically detect `backend/Dockerfile` and build the Python FastAPI app.
   - Add your necessary environment variables (`DATABASE_URL`, `GEMINI_API_KEY`, etc.).
2. **Deploy the Frontend:** 
   - Create another **Web Service** pointing to the `/frontend` directory.
   - The platform will detect `frontend/Dockerfile` and build the Next.js app in standalone mode.
   - **Crucially**, add the `NEXT_PUBLIC_API_URL` environment variable pointing to the public URL of your *deployed backend service*.

*Note: The frontend uses a multi-stage standalone Dockerfile optimized for Next.js, and the backend relies on an optimized `python:3.12-slim` image.*
