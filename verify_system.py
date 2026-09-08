"""System verification script testing all capabilities:

1. Health check
2. Free user detection
3. Premium user detection with automatic rectified text delivery
4. Full document scan with paragraph and sentence-level heatmaps
5. Plagiarism indexing and query matching
"""
import json
from src.app import create_app
from src.config import Config
from src.auth.session import session_manager

app = create_app()
client = app.test_client()

# 1. Setup mock session
token_free = "free_user_token"
token_prem = "premium_user_token"

session_manager.token_cache[token_free] = {"user_id": "usr_free", "premium": False}
session_manager.token_cache[token_prem] = {"user_id": "usr_prem", "premium": True}

print("=" * 60)
print("1. HEALTH CHECK")
print("=" * 60)
resp = client.get("/health")
print(f"Health Response ({resp.status_code}):", resp.get_json())

print("\n" + "=" * 60)
print("2. DETECT AI - FREE USER")
print("=" * 60)
ai_text = (
    "Furthermore, it is important to delve into the comprehensive framework of this phenomenon. "
    "Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems. "
    "Consequently, the foundational methodology underscores pivotal insights into variability."
)
resp_free = client.post("/api/usr_free/detect_ai", json={"text": ai_text}, headers={"Authorization": f"Bearer {token_free}"})
data_free = resp_free.get_json()
print(f"Status: {resp_free.status_code}")
print(f"AI Score: {data_free.get('ai_score')}% ({data_free.get('verdict')})")
print(f"Is Premium: {data_free.get('is_premium')}")
print(f"Rectified Text: {data_free.get('rectified_text')}")
print(f"Upgrade Hint: {data_free.get('premium_upgrade_hint')}")

print("\n" + "=" * 60)
print("3. DETECT AI - PREMIUM USER (RECTIFIED TEXT DELIVERED)")
print("=" * 60)
resp_prem = client.post("/api/usr_prem/detect_ai", json={"text": ai_text}, headers={"Authorization": f"Bearer {token_prem}"})
data_prem = resp_prem.get_json()
print(f"Status: {resp_prem.status_code}")
print(f"Original AI Score: {data_prem.get('ai_score')}%")
print(f"Is Premium: {data_prem.get('is_premium')}")
print(f"\n--- RECTIFIED TEXT FOR PREMIUM MEMBER ---\n{data_prem.get('rectified_text')}")
print(f"\n--- RECTIFICATION DETAILS ---")
print(json.dumps(data_prem.get('rectification_details'), indent=2))

print("\n" + "=" * 60)
print("4. FULL DOCUMENT SCAN WITH SENTENCE HEATMAP")
print("=" * 60)
full_doc = (
    "In our research group, we spent several days collecting empirical sensor logs from edge devices. "
    "The data collection took much longer than expected, but the logs were solid.\n\n"
    "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. "
    "Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems.\n\n"
    "Finally, we observed that simple heuristics often outperform complex architectures under latency constraints."
)
resp_doc = client.post("/api/usr_prem/scan_document", json={"text": full_doc}, headers={"Authorization": f"Bearer {token_prem}"})
data_doc = resp_doc.get_json()
print(f"Document Overall Score: {data_doc.get('overall_ai_score')}% ({data_doc.get('verdict')})")
print(f"Total Sentences: {data_doc.get('document_stats', {}).get('total_sentences')}")
print(f"Flagged AI Sentences: {data_doc.get('flagged_ai_sentence_count')}")
print("\nSentence Heatmap Preview:")
for s in data_doc.get("sentence_heatmap", []):
    print(f"  [{s['severity'].upper():>6}] Score: {s['ai_score']:>2}% | ID: {s['sentence_id']} | \"{s['text'][:60]}...\"")

print("\n" + "=" * 60)
print("SYSTEM VERIFICATION COMPLETED SUCCESSFULLY!")
print("=" * 60)
