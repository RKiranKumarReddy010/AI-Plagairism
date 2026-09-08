# AI Plagiarism & Robust Detection Engine with Premium Text Rectification

An enterprise-grade, high-precision AI content detector, exact & semantic plagiarism engine, and intelligent text rectifier designed for full-document processing.

---

## 📁 Architecture

```
ColabVM/
├── src/
│   ├── config.py                 # Centralized configuration & hyperparameter tuning
│   ├── core/
│   │   ├── preprocessor.py       # LaTeX, unicode, math symbols, and smart quote normalization
│   │   └── chunker.py            # Hierarchical document chunker (documents -> paragraphs -> sentences)
│   ├── detector/
│   │   ├── ai_detector.py        # Multi-signal AI detector (burstiness CV, lexical markers, TTR, rhythm)
│   │   └── doc_analyzer.py       # Full-document hierarchical analyzer & sentence heatmap generator
│   ├── plagiarism/
│   │   ├── winnowing.py          # Verbatim plagiarism detection (k-gram shingling & winnowing)
│   │   └── semantic.py           # FAISS semantic vector search (cosine similarity via inner product)
│   ├── rectifier/
│   │   └── text_rectifier.py     # Contextual AI-to-human text rectifier & rhythm transformer
│   ├── auth/
│   │   └── session.py            # Token caching, Firebase DB auth, & role verification
│   ├── services/
│   │   └── doc_service.py        # Unified orchestration layer
│   ├── api/
│   │   └── routes.py             # Flask Blueprint with validation and endpoints
│   └── app.py                    # Application factory (create_app)
├── main.py                       # WSGI entrypoint with backwards compatibility
├── verify_system.py              # End-to-end integration verification runner
├── test_api.py                   # API sample test client
├── tests/                        # Full automated unit test suite (22 tests)
└── .env                          # Environment secrets and server configuration
```

---

## 🚀 Key Features

1. **Full-Document Hierarchical Processing**:
   - Capable of analyzing multi-page documents (thousands of words) without truncation.
   - Decomposes documents into structured paragraphs and sentences with offset tracking.
   - Generates granular sentence-by-sentence AI heatmaps (`LOW`, `MEDIUM`, `HIGH`) with pinpointed marker indicators.

2. **Premium Text Rectification**:
   - For premium members, the system transforms robotic AI sentences into natural human writing.
   - Eliminates dead-giveaway phrases (`"delve into"`, `"testament to"`, `"pivotal role"`).
   - Injects natural sentence rhythm, natural contractions, and varied starters.
   - Returns complete `rectified_text` alongside before-and-after score reductions (e.g. 100% -> 55%).

3. **Hybrid Plagiarism Engine**:
   - **Winnowing Algorithm**: Substring exact and near-verbatim fingerprint matching.
   - **FAISS Semantic Vector Search**: Paraphrase and concept-level match detection.

---

## 📡 API Reference

### 1. Primary AI Detection & Rectification
- **Endpoint**: `POST /api/<user_id>/detect_ai`
- **Headers**: `Authorization: Bearer <token>` or master API key
- **Payload**: `{"text": "..."}`
- **Response**:
  - `ai_score`: Score 0–100
  - `verdict`: `LIKELY AI-GENERATED` | `INCONCLUSIVE / MIXED` | `LIKELY HUMAN-WRITTEN`
  - `report`: Formatted diagnostic report
  - `rectified_text`: **(Premium Only)** Full humanized text with AI markers replaced and sentence rhythm smoothed.
  - `rectification_details`: Before-and-after score comparison and change list.

### 2. Full Document Scan
- **Endpoint**: `POST /api/<user_id>/scan_document`
- **Payload**: `{"text": "...", "check_plagiarism": true}`
- **Response**:
  - `overall_ai_score`: Aggregated score
  - `document_stats`: Word, paragraph, and sentence counts
  - `sentence_heatmap`: Array of all sentences with individual AI probability and severity rating.
  - `rectified_text`: Rectified version of the entire document (Premium).

### 3. Dedicated Text Rectification
- **Endpoint**: `POST /api/<user_id>/rectify_text`
- **Headers**: `Authorization: Bearer <premium_token>`
- **Payload**: `{"text": "..."}`
- **Response**: Direct rectified text, modification count, and score reduction metrics.

### 4. Plagiarism Indexing
- **Endpoint**: `POST /api/<user_id>/index_document`
- **Payload**: `{"doc_id": "doc_123", "text": "..."}`

---

## 🧪 Testing & Verification

Run the complete test suite:
```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Run the end-to-end system verification:
```powershell
.\venv\Scripts\python.exe verify_system.py
```
