# AI Trust Scraper Ecosystem

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)
![React](https://img.shields.io/badge/React-18+-61dafb.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A production-grade, multi-source data scraping pipeline and content trust-scoring ecosystem. This project was engineered to aggregate AI-related content from diverse platforms (Blogs, YouTube, PubMed), rigorously evaluate their credibility through a mathematical scoring model, and present the structured data via a beautiful, real-time React dashboard.

---

## 📋 Assignment Requirements Checklist

This project was built to strictly adhere to the technical assignment constraints:

- [x] **Task 1: Multi-Source Scraper**
  - Scrapes exactly 3 blog posts, 2 YouTube videos, and 1 PubMed article.
  - Generates the single required `scraped_data.json` containing all 6 sources.
  - Schema strictly matches the requested format (`source_url`, `trust_score`, `content_chunks`, etc.).
  - Auto-extracts author, published date, and generates dynamic `topic_tags`.

- [x] **Task 2: Trust Score System Design**
  - Mathematical algorithm calculating credibility (0.00 – 1.00).
  - Evaluates: Author Credibility, Citation/View Count, Domain Authority, Recency, and Medical Disclaimers.
  - Handles edge cases (missing dates, no authors) and implements abuse prevention logic (SEO spam penalties).
  - See the `REPORT.md` file for an in-depth explanation of the scoring architecture.

---

## 🏗️ Architecture & Features

### 1. Multi-Source Ingestion (`scraper/`)
* **Blogs**: Parses HTML dynamically using `BeautifulSoup4`. Filters out navigation, headers, and ads to strictly extract article content and metadata.
* **YouTube**: Employs `youtube-transcript-api` to securely fetch video captions alongside channel authority and view counts.
* **PubMed**: Leverages the NCBI E-utilities REST API to extract peer-reviewed medical abstracts, managing API rate limits with exponential backoff logic.

### 2. Natural Language Processing (`utils/`)
* **Chunking**: Intelligently splits massive texts into optimized, logical paragraphs without breaking sentence structure. This prepares the data for seamless LLM ingestion downstream.
* **Auto-Tagging**: A heuristic-based scanner that analyzes scraped text for high-frequency domain keywords to categorize articles accurately.

### 3. Trust Evaluation Engine (`scoring/trust_score.py`)
A deterministic mathematical model prioritizing high-quality journalism and peer-reviewed research. It rewards established organizations (`TRUSTED_ORGS`) and penalizes outdated content via an exponential decay function.

### 4. Interactive Dashboard (`frontend/`)
A premium React/Vite web application that acts as your data command center. Features real-time statistics, deep search, trust-score sorting, and automated execution of the backend pipeline.

---

## 🚀 Installation & Usage

This project features a **Single Server Architecture**. The FastAPI backend automatically serves the React frontend, meaning you only need to run one process.

### Prerequisites
* **Python 3.10+**
* **Node.js 18+**

### Quick Start (Windows)
We have included an automated setup script that installs all dependencies, builds the React frontend, and launches the FastAPI server.

1. Clone the repository and navigate into the folder:
   ```powershell
   git clone https://github.com/asm59-345/Ai_Data_Scraper.git
   cd Ai_Data_Scraper/ai-trust-scraper
   ```

2. Run the single-server startup script:
   ```powershell
   .\start-single-server.ps1
   ```

3. Open your browser and navigate to:
   👉 **http://localhost:8000**

### Development Mode (Split Servers)
If you prefer to run the backend and frontend separately for hot-reloading during development:

1. **Start the FastAPI Backend:**
   ```powershell
   python -m uvicorn backend.api:app --reload --port 8000
   ```

2. **Start the Vite Frontend:**
   Open a second terminal and run:
   ```powershell
   cd frontend
   npm run dev
   ```

3. Open your browser and navigate to the frontend dev server:
   👉 **http://localhost:5173/**

*(If you are on Mac/Linux, the commands are the same once you have run `npm install` and `pip install -r requirements.txt`.)*

---

## 📂 Output Format Example

The pipeline generates the final output at `output/scraped_data.json` matching the exact schema requested:

```json
{
  "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
  "source_type": "pubmed",
  "title": "Machine Learning in Healthcare",
  "author": "Dr. John Doe",
  "published_date": "2023-10-01T00:00:00Z",
  "language": "en",
  "region": "US",
  "topic_tags": ["AI", "Healthcare", "Research"],
  "trust_score": 0.95,
  "content_chunks": [
    "Abstract sentence 1...",
    "Abstract sentence 2..."
  ]
}
```
---

## 🧠 Known Limitations
* **YouTube Captions**: If a creator explicitly disables captions, the scraper gracefully falls back to using the video description.
* **PubMed Rate Limits**: NCBI limits queries to 3 requests/second. The scraper handles this safely using `asyncio.sleep()`.

---
*Developed for the AI Data Scraper Engineering Assignment by Ashmit Gautam .*
