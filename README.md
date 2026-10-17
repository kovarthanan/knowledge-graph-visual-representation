# 🕸️ Ratan Tata · Knowledge Graph RAG

Ask questions about **Ratan Tata** and see exactly which part of a **Neo4j knowledge graph** produced the answer.

The app retrieves facts from the graph, then a **local LLM (Qwen 2.5 via Ollama)** writes the answer. An interactive **PyVis** network shows only the nodes connected to your question, next to the raw Cypher query that was run.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Neo4j](https://img.shields.io/badge/Neo4j-Aura-008CC1) ![Ollama](https://img.shields.io/badge/LLM-Ollama%20Qwen%202.5-black) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B)

---

## ✨ Features

- **Knowledge graph in Neo4j:** `Person → Topic → FAQ → Answer`, built from a plain `FAQ.txt`
- **Graph RAG:** keyword-scored Cypher retrieval plus a grounded LLM answer ("I don't know" when the graph has no facts)
- **Live query subgraph:** each question draws only its matched nodes, with an animated left-to-right layout
- **Transparent retrieval:** shows the exact Cypher sent to Neo4j, and a query you can paste into Neo4j Browser
- **Engaging flow:** searching → graph appears → answer streams token by token
- **Single-screen dashboard:** 💬 Chat | 🕸️ Graph | 🔎 Query
- **Runs locally:** no OpenAI key needed

---

## 🏗️ Architecture

```
FAQ.txt ──► parse ──► Neo4j Aura (knowledge graph)
                            │
   question ──► keywords ──► Cypher search (scored) ──► top facts
                                                          │
                       ┌──────────────────────────────────┤
                       ▼                                  ▼
            PyVis subgraph (only matched nodes)     Ollama · Qwen 2.5
                                                          │
                                                   streamed answer
```

**Graph model**

```
(:Person {name})-[:HAS_TOPIC]->(:Topic {name})-[:HAS_FAQ]->(:FAQ {question})-[:HAS_ANSWER]->(:Answer {text})
```

---

## 📁 Project structure

```
.
├── app.py             # Streamlit dashboard (chat, PyVis graph, Cypher panel)
├── kg_rag.py          # Graph loading, retrieval and RAG chain (also a terminal chat)
├── FAQ.txt            # Source knowledge: 24 Q&A pairs about Ratan Tata
├── requirements.txt
├── .env.example       # Neo4j + model settings template
└── .streamlit/
    └── config.toml    # Theme
```

---

## 🚀 Getting started

### 1. Prerequisites
- Python 3.10+
- A free [Neo4j Aura](https://console.neo4j.io) instance
- [Ollama](https://ollama.com/download) running locally

### 2. Install
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
ollama pull qwen2.5:1.5b
```

### 3. Configure
Copy `.env.example` to `.env` and fill in your Neo4j Aura details:
```
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
LLM_MODEL=qwen2.5:1.5b
```

### 4. Load the graph (first time)
```bash
python kg_rag.py
```
This parses `FAQ.txt`, loads it into Neo4j and opens a terminal chat (type `quit` to exit).

### 5. Run the app
```bash
streamlit run app.py
```

---

## 💬 Try these questions

| Question | Graph result |
|----------|--------------|
| *Tell me about his acquisitions, the Nano car, awards and philanthropy* | 5 FAQs across 4 topics |
| *Tell me about his education, awards and philanthropy* | 5 FAQs across 3 topics |
| *What did he acquire abroad?* | Tetley and Corus via Acquisitions |
| *Who is Ratan Tata?* | General overview |

---

## 🔍 Explore the graph in Neo4j Browser

```cypher
MATCH p=(:Person)-[:HAS_TOPIC]->(:Topic)-[:HAS_FAQ]->(:FAQ)-[:HAS_ANSWER]->(:Answer)
RETURN p
```

---

## 🛠️ Tech stack

| Layer | Tools |
|-------|-------|
| Graph DB | Neo4j Aura, Cypher |
| LLM | Ollama · Qwen 2.5 (1.5B), LangChain |
| Visualisation | PyVis (vis-network) |
| UI | Streamlit |

---

## ⚠️ Notes

- Retrieval is keyword-based, so phrase questions with words used in the FAQs (acquisition, Nano, awards…).
- `FAQ.txt` content is a summary for learning purposes; verify facts with official sources.
- Answer speed depends on your hardware, since the LLM runs locally.

---

Built as a learning project on Knowledge Graph RAG with LangChain, Neo4j and local LLMs.
