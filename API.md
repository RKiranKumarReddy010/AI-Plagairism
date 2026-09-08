# API Documentation: AI Plagiarism Detection & Premium Text Rectification

A complete reference for all available endpoints, authentication requirements, request payloads, response schemas, and code examples.

---

## 📑 Table of Contents
1. [Base URL & Authentication](#-base-url--authentication)
2. [Core Status Endpoints](#-core-status-endpoints)
   - [GET /](#1-get---api-discovery)
   - [GET /health](#2-get-health---health-check)
3. [User & Subscription Endpoints](#-user--subscription-endpoints)
   - [POST /api/register](#3-post-apiregister---register-user)
   - [POST /api/login](#4-post-apilogin---login-user)
   - [GET /api/{user_id}/check](#5-get-apiuser_idcheck---check-premium-status)
   - [POST /api/{user_id}/activate](#6-post-apiuser_idactivate---activate-premium)
   - [POST /api/{user_id}/call](#7-post-apiuser_idcall---server-verification)
4. [AI Detection & Document Scanning Endpoints](#-ai-detection--document-scanning-endpoints)
   - [POST /api/{user_id}/detect_ai](#8-post-apiuser_iddetect_ai---ai-detection--rectification)
   - [POST /api/{user_id}/scan_document](#9-post-apiuser_idscan_document---full-document-heatmap-scan)
5. [Premium Rectification & Plagiarism Endpoints](#-premium-rectification--plagiarism-endpoints)
   - [POST /api/{user_id}/rectify_text](#10-post-apiuser_idrectify_text---dedicated-text-rectifier)
   - [POST /api/{user_id}/index_document](#11-post-apiuser_idindex_document---index-reference-document)
6. [Cashfree Payment Gateway Endpoints](#-cashfree-payment-gateway-endpoints)
   - [POST /api/payment/create_order](#12-post-apipaymentcreate_order---create-cashfree-order)
   - [POST /api/payment/verify_order](#13-post-apipaymentverify_order---verify-order--activate-premium)
   - [GET /api/config](#14-get-apiconfig---public-client-configurations)
7. [Response Codes & Error Handling](#-response-codes--error-handling)

---

## 🔐 Base URL & Authentication

### Base URL
```
http://127.0.0.1:5000
```

### Authentication Methods
Endpoints that require authorization accept one of the following in the `Authorization` HTTP header:

1. **Bearer Session Token** (Standard users and premium members):
   ```http
   Authorization: Bearer <session_token>
   ```
2. **Master Firebase API Key** (Admin / system integration):
   ```http
   Authorization: AIzaSyB9ouZqk4pxpx9sIyleteZR1O8vTDasT3c
   ```
   *(Requests using the master API key are automatically granted full premium permissions).*

---

## 🌐 Core Status Endpoints

### 1. `GET /` - API Discovery
Returns service status, version, and the list of available API routes.

- **Method**: `GET`
- **Authentication**: None
- **Response (200 OK)**:
```json
{
  "service": "AI Plagiarism Detection & Premium Text Rectification API",
  "version": "2.0.0",
  "status": "online",
  "endpoints": [
    "/api/register",
    "/api/login",
    "/api/<user_id>/check",
    "/api/<user_id>/activate",
    "/api/<user_id>/detect_ai",
    "/api/<user_id>/scan_document",
    "/api/<user_id>/rectify_text",
    "/api/<user_id>/index_document",
    "/api/<user_id>/call"
  ]
}
```

---

### 2. `GET /health` - Health Check
Liveness and uptime verification check.

- **Method**: `GET`
- **Authentication**: None
- **Response (200 OK)**:
```json
{
  "status": "healthy"
}
```

---

## 👤 User & Subscription Endpoints

### 3. `POST /api/register` - Register User
Creates a new user profile with free status in the database.

- **Method**: `POST`
- **Authentication**: None
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "email": "researcher@example.com",
  "password": "SecurePassword123!",
  "name": "Dr. Jane Doe"
}
```
- **Response (201 Created)**:
```json
{
  "status": "success",
  "message": "User registered.",
  "user_id": "usr_9a4f210b"
}
```
- **Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "message": "Email already registered."
}
```

---

### 4. `POST /api/login` - Login User
Authenticates user credentials and generates a session token.

- **Method**: `POST`
- **Authentication**: None
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "email": "researcher@example.com",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK)**:
```json
{
  "status": "success",
  "token": "4f18d2a6c0b39e71f8b417c82305e94b2a8d11c0f83e29a90b4d21109a",
  "user_id": "usr_9a4f210b",
  "premium": false
}
```
- **Error Response (401 Unauthorized)**:
```json
{
  "status": "error",
  "message": "Invalid credentials."
}
```

---

### 5. `GET /api/{user_id}/check` - Check Premium Status
Retrieves current subscription status for a specific user.

- **Method**: `GET`
- **Authentication**: Required (`Bearer <token>` or Master API Key)
- **Response (200 OK)**:
```json
{
  "status": "success",
  "user_id": "usr_9a4f210b",
  "premium": true
}
```

---

### 6. `POST /api/{user_id}/activate` - Activate Premium
Upgrades user account to the Premium tier in both Firebase DB and session memory.

- **Method**: `POST`
- **Authentication**: Required (`Bearer <token>` or Master API Key)
- **Response (200 OK)**:
```json
{
  "status": "success",
  "message": "Premium activated for usr_9a4f210b."
}
```

---

### 7. `POST /api/{user_id}/call` - Server Verification
Validates that incoming server requests correspond to the authorized `CURRENT_SERVER_ID`.

- **Method**: `POST` or `GET`
- **Authentication**: Required
- **Response (200 OK)**:
```json
{
  "status": "success",
  "message": "Verified call processed for user usr_456."
}
```

---

## 🔍 AI Detection & Document Scanning Endpoints

### 8. `POST /api/{user_id}/detect_ai` - AI Detection & Rectification
The primary detection endpoint. Evaluates text probability for AI generation using lexical markers, burstiness, cadence uniformity, and Type-Token Ratio.

> [!NOTE]
> For **Premium Members**, this endpoint automatically generates and returns the **`rectified_text`**, alongside before-and-after improvement metrics and score reduction.

- **Method**: `POST`
- **Authentication**: Required (`Bearer <token>` or Master API Key)
- **Headers**:
  - `Authorization: Bearer <token>` (or `Authorization: <FIREBASE_API_KEY>`)
  - `Content-Type: application/json` (also supports `text/plain` or form data)
- **Request Body**:
```json
{
  "text": "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems. Consequently, the foundational methodology underscores pivotal insights into variability."
}
```

#### Free Tier Response (200 OK):
```json
{
  "status": "success",
  "ai_score": 100,
  "verdict": "LIKELY AI-GENERATED",
  "is_premium": false,
  "premium_upgrade_hint": "Upgrade to Premium to receive complete, automatically rectified humanized text.",
  "report": "Verdict: LIKELY AI-GENERATED (confidence: 100%)\nWord count: 35\nSentences analyzed: 3\nBurstiness CV: 0.220 (human ~0.7+, AI ~0.3-0.4)\nType-token ratio: 0.857\nAI markers found: furthermore, delve, comprehensive, framework, phenomenon, moreover, paradigm, testament, multifaceted, foundational, methodology, underscores, pivotal, variability\n\nReasons:\n  - AI academic/rhetorical markers detected: ['delve', 'moreover', 'pivotal']\n  - Typical LLM canned phrases detected: ['serves as a testament to']\n  - Uniform sentence cadence (CV: 0.22)",
  "metrics": {
    "burstiness_cv": 0.22,
    "sentence_stddev": 2.52,
    "type_token_ratio": 0.8571,
    "ai_markers_found": ["furthermore", "delve", "comprehensive", "framework", "phenomenon", "moreover", "paradigm", "testament", "multifaceted", "foundational", "methodology", "underscores", "pivotal", "variability"],
    "human_markers_found": [],
    "robotic_phrases_found": ["serves as a testament to"],
    "sentence_count": 3,
    "word_count": 35
  },
  "fix": [
    "Vary your sentence lengths. Mix short punchy sentences with longer descriptive ones.",
    "Your vocabulary is overly varied. Repeat key terms naturally instead of constantly using formal synonyms.",
    "Replace 'delve' with 'explore'",
    "Replace 'pivotal' with 'key'",
    "Replace 'multifaceted' with 'complex'",
    "Replace 'testament' with 'clear proof'",
    "Add conversational discourse markers, personal perspective, or rhetorical phrasing to break robotic cadence."
  ]
}
```

#### Premium Tier Response (200 OK) - Includes `rectified_text`:
```json
{
  "status": "success",
  "ai_score": 100,
  "verdict": "LIKELY AI-GENERATED",
  "is_premium": true,
  "rectified_text": "Also, it's key to look into the thorough structure of this event. In addition, this model proves the complex nature of modern environments. As a result, the basic approach highlights key insights into variation.",
  "rectification_details": {
    "original_ai_score": 100,
    "rectified_ai_score": 55,
    "score_reduction": 45,
    "modifications_count": 17,
    "sample_changes": [
      {
        "sentence_id": "p0_s0",
        "original": "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon.",
        "rectified": "Also, it's key to look into the thorough structure of this event.",
        "modifications": [
          "Replaced robotic phrase 'delve into' with 'look into'",
          "Replaced AI buzzword 'comprehensive' with 'thorough'",
          "Replaced AI buzzword 'furthermore' with 'also'",
          "Replaced AI buzzword 'framework' with 'structure'",
          "Replaced AI buzzword 'phenomenon' with 'event'",
          "Replaced AI buzzword 'crucial' with 'key'",
          "Naturalized phrasing 'it is' to 'it's'"
        ]
      }
    ]
  },
  "report": "...",
  "metrics": { "..." : "..." }
}
```

---

### 9. `POST /api/{user_id}/scan_document` - Full Document Heatmap Scan
Designed for processing entire documents of arbitrary length (multi-page reports, papers, and essays). Parses documents hierarchically, calculates sentence-level risk heatmaps, and checks against indexed plagiarism repositories.

- **Method**: `POST`
- **Authentication**: Required (`Bearer <token>` or Master API Key)
- **Request Body**:
```json
{
  "text": "In our laboratory research group, we spent several days collecting empirical sensor logs from edge nodes. The data collection took much longer than expected, but the logs were solid.\n\nFurthermore, it is crucial to delve into the comprehensive framework of this phenomenon. Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems.\n\nFinally, we observed that simple heuristics often outperform complex architectures under tight latency constraints.",
  "check_plagiarism": true
}
```

- **Response (200 OK)**:
```json
{
  "status": "success",
  "overall_ai_score": 74,
  "verdict": "LIKELY AI-GENERATED",
  "document_stats": {
    "total_words": 62,
    "total_paragraphs": 3,
    "total_sentences": 5
  },
  "flagged_ai_sentence_count": 2,
  "flagged_ratio": 0.4,
  "sentence_heatmap": [
    {
      "sentence_id": "p0_s0",
      "paragraph_id": 0,
      "index_in_para": 0,
      "text": "In our laboratory research group, we spent several days collecting empirical sensor logs from edge nodes.",
      "ai_score": 47,
      "severity": "medium",
      "is_flagged": false,
      "ai_markers": ["empirical"],
      "robotic_phrases": [],
      "char_start": 0,
      "char_end": 105
    },
    {
      "sentence_id": "p0_s1",
      "paragraph_id": 0,
      "index_in_para": 1,
      "text": "The data collection took much longer than expected, but the logs were solid.",
      "ai_score": 25,
      "severity": "low",
      "is_flagged": false,
      "ai_markers": [],
      "robotic_phrases": [],
      "char_start": 106,
      "char_end": 182
    },
    {
      "sentence_id": "p1_s0",
      "paragraph_id": 1,
      "index_in_para": 0,
      "text": "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon.",
      "ai_score": 75,
      "severity": "high",
      "is_flagged": true,
      "ai_markers": ["furthermore", "delve", "comprehensive", "framework", "phenomenon", "crucial"],
      "robotic_phrases": ["delve into"],
      "char_start": 184,
      "char_end": 272
    },
    {
      "sentence_id": "p1_s1",
      "paragraph_id": 1,
      "index_in_para": 1,
      "text": "Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems.",
      "ai_score": 100,
      "severity": "high",
      "is_flagged": true,
      "ai_markers": ["moreover", "paradigm", "testament", "multifaceted", "ecosystems"],
      "robotic_phrases": ["serves as a testament to"],
      "char_start": 273,
      "char_end": 367
    },
    {
      "sentence_id": "p2_s0",
      "paragraph_id": 2,
      "index_in_para": 0,
      "text": "Finally, we observed that simple heuristics often outperform complex architectures under tight latency constraints.",
      "ai_score": 25,
      "severity": "low",
      "is_flagged": false,
      "ai_markers": [],
      "robotic_phrases": [],
      "char_start": 369,
      "char_end": 484
    }
  ],
  "paragraph_analysis": [
    {
      "paragraph_id": 0,
      "word_count": 27,
      "sentence_count": 2,
      "ai_score": 36,
      "verdict": "CLEAN",
      "text_preview": "In our laboratory research group, we spent several days collecting empirical sensor logs from edge nodes. The data colle..."
    },
    {
      "paragraph_id": 1,
      "word_count": 25,
      "sentence_count": 2,
      "ai_score": 88,
      "verdict": "HIGH RISK",
      "text_preview": "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. Moreover, this paradigm serves..."
    },
    {
      "paragraph_id": 2,
      "word_count": 14,
      "sentence_count": 1,
      "ai_score": 25,
      "verdict": "CLEAN",
      "text_preview": "Finally, we observed that simple heuristics often outperform complex architectures under tight latency constraints."
    }
  ],
  "is_premium": true,
  "rectified_text": "In our laboratory research group, we spent several days collecting practical sensor logs from edge nodes. The data collection took much longer than expected, but the logs were solid.\n\nAlso, it's key to look into the thorough structure of this event. In addition, this model proves the complex nature of modern environments.\n\nFinally, we observed that simple heuristics often outperform complex architectures under tight latency constraints."
}
```

---

## 🛠️ Premium Rectification & Plagiarism Endpoints

### 10. `POST /api/{user_id}/rectify_text` - Dedicated Text Rectifier
Directly transforms flagged text into humanized text, eliminating robotic structures and optimizing sentence cadence.

- **Method**: `POST`
- **Authentication**: Required (`Bearer <premium_token>` or Master API Key)
- **Restrictions**: Exclusive to **Premium Members**.
- **Request Body**:
```json
{
  "text": "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems."
}
```
- **Response (200 OK)**:
```json
{
  "status": "success",
  "rectified_text": "Also, it's key to look into the thorough structure of this event. In addition, this model proves the complex nature of modern environments.",
  "original_ai_score": 100,
  "rectified_ai_score": 55,
  "score_reduction": 45,
  "modifications_count": 12,
  "modifications": [
    "Replaced robotic phrase 'delve into' with 'look into'",
    "Replaced robotic phrase 'serves as a testament to' with 'proves'",
    "Replaced AI buzzword 'comprehensive' with 'thorough'",
    "Replaced AI buzzword 'furthermore' with 'also'",
    "Replaced AI buzzword 'framework' with 'structure'",
    "Replaced AI buzzword 'phenomenon' with 'event'",
    "Replaced AI buzzword 'multifaceted' with 'complex'",
    "Replaced AI buzzword 'moreover' with 'in addition'",
    "Replaced AI buzzword 'paradigm' with 'model'",
    "Replaced AI buzzword 'ecosystems' with 'environments'",
    "Replaced AI buzzword 'crucial' with 'key'",
    "Naturalized phrasing 'it is' to 'it's'"
  ],
  "sentence_comparisons": [
    {
      "sentence_id": "p0_s0",
      "original": "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon.",
      "rectified": "Also, it's key to look into the thorough structure of this event.",
      "modifications": [
        "Replaced robotic phrase 'delve into' with 'look into'",
        "Replaced AI buzzword 'comprehensive' with 'thorough'",
        "Replaced AI buzzword 'furthermore' with 'also'",
        "Replaced AI buzzword 'framework' with 'structure'",
        "Replaced AI buzzword 'phenomenon' with 'event'",
        "Replaced AI buzzword 'crucial' with 'key'",
        "Naturalized phrasing 'it is' to 'it's'"
      ]
    }
  ]
}
```
- **Error Response if Non-Premium (403 Forbidden)**:
```json
{
  "status": "error",
  "message": "Text rectification is an exclusive premium feature. Please upgrade your account."
}
```

---

### 11. `POST /api/{user_id}/index_document` - Index Reference Document
Indexes an original source document into both the Winnowing lexical fingerprint database and the FAISS semantic vector space for plagiarism comparison.

- **Method**: `POST`
- **Authentication**: Required (`Bearer <token>` or Master API Key)
- **Request Body**:
```json
{
  "doc_id": "ref_paper_2026",
  "text": "The quick brown fox jumps over the lazy dog and establishes a foundational metric for wildlife observations."
}
```
```json
{
  "status": "success",
  "message": "Document 'ref_paper_2026' indexed successfully."
}
```

---

## 💳 Cashfree Payment Gateway Endpoints

### 12. `POST /api/payment/create_order` - Create Cashfree Order
Initializes a payment order session via the Cashfree PG API (`POST https://api.cashfree.com/pg/orders`) and returns the `payment_session_id` needed by the Cashfree JS SDK v3.

- **Method**: `POST`
- **Authentication**: Required (`Bearer <token>`)
- **Request Body**:
```json
{
  "email": "user@example.com",
  "name": "Jane Doe",
  "phone": "9876543210",
  "amount": 499.0
}
```
- **Response (200 OK)**:
```json
{
  "status": "success",
  "message": "Order created successfully.",
  "order": {
    "order_id": "order_1725752391_a1b2c3",
    "payment_session_id": "session_m_98f12a...",
    "order_status": "ACTIVE",
    "order_amount": 499.0,
    "order_currency": "INR",
    "environment": "production"
  }
}
```

---

### 13. `POST /api/payment/verify_order` - Verify Order & Activate Premium
Queries Cashfree (`GET https://api.cashfree.com/pg/orders/{order_id}`) to confirm that the customer successfully completed the payment. If status is `PAID`, automatically upgrades user to `premium: true` in Firebase.

- **Method**: `POST`
- **Authentication**: Required (`Bearer <token>`)
- **Request Body**:
```json
{
  "order_id": "order_1725752391_a1b2c3"
}
```
- **Response (200 OK)**:
```json
{
  "status": "success",
  "message": "Payment verified! Premium activated successfully.",
  "data": {
    "order_id": "order_1725752391_a1b2c3",
    "order_status": "PAID",
    "premium": true,
    "activated": true
  }
}
```

---

### 14. `GET /api/config` - Public Client Configurations
Returns client-side configuration parameters including Firebase project credentials, Cashfree AppID, and subscription pricing.

- **Method**: `GET`
- **Authentication**: None
- **Response (200 OK)**:
```json
{
  "cashfree": {
    "appId": "13924675754e08d7fe743e5d52e7642931",
    "environment": "production"
  },
  "firebase": {
    "apiKey": "AIzaSyB9ouZqk4pxpx9sIyleteZR1O8vTDasT3c",
    "appId": "1:513232699098:web:0c5a3e28cdc75e7627efe3",
    "authDomain": "rdm-omnitensor.firebaseapp.com",
    "messagingSenderId": "513232699098",
    "projectId": "rdm-omnitensor",
    "storageBucket": "rdm-omnitensor.firebasestorage.app"
  },
  "pricing": {
    "premium_inr": 499.0
  }
}
```

---

## 📊 Response Codes & Error Handling

All error responses adhere to the standard format:
```json
{
  "status": "error",
  "message": "Descriptive explanation of the error."
}
```

| HTTP Status Code | Meaning | Common Causes |
| :--- | :--- | :--- |
| **`200 OK`** | Success | Request was processed normally. |
| **`201 Created`** | Created | User was successfully registered. |
| **`400 Bad Request`** | Input validation failure | Missing `text` field, missing credentials, or email already registered. |
| **`401 Unauthorized`** | Authentication missing or invalid | Invalid session token or missing `Authorization` header. |
| **`403 Forbidden`** | Permission denied | Non-premium user attempting to access `/rectify_text` or user ID mismatch. |
| **`404 Not Found`** | Endpoint missing | Incorrect URL path. |
| **`500 Internal Error`** | Server error | Unexpected processing exception or external database connection failure. |

---

## 💻 Code Examples

### Python (`requests`)
```python
import requests

API_KEY = "AIzaSyB9ouZqk4pxpx9sIyleteZR1O8vTDasT3c"
BASE_URL = "http://127.0.0.1:5000"

# 1. Detect AI and receive rectified text (using master API key)
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}
payload = {
    "text": "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon."
}

response = requests.post(f"{BASE_URL}/api/usr_456/detect_ai", json=payload, headers=headers)
data = response.json()

print("Original AI Score:", data["ai_score"])
print("Rectified Text:", data.get("rectified_text"))
```

### cURL
```bash
# Full Document Scan
curl -X POST "http://127.0.0.1:5000/api/usr_456/scan_document" \
     -H "Authorization: AIzaSyB9ouZqk4pxpx9sIyleteZR1O8vTDasT3c" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Furthermore, it is crucial to delve into the multifaceted nature of modern ecosystems."
     }'
```

### PowerShell (`Invoke-RestMethod`)
```powershell
$apiKey = "AIzaSyB9ouZqk4pxpx9sIyleteZR1O8vTDasT3c"
$body = @{
    text = "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon."
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/usr_456/detect_ai" `
                              -Method POST `
                              -ContentType "application/json" `
                              -Headers @{ Authorization = $apiKey } `
                              -Body $body

$response.ai_score
$response.rectified_text
```
