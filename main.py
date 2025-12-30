import requests
from datetime import datetime
import json
import re

API_BASE = "https://data.europarl.europa.eu/api/v2"
START_DATE = "2025-07-01"  # Filter from this date
YEAR = "2025"

# --- Fonctions d'extraction (adapted for API data) ---
def extract_inter_institutional_code(title):
    match = re.search(r'\b(\d{4}/\d{4}\([A-Z]+\))\b', title)
    return match.group(1) if match else ""

def extract_document_reference(identifier):
    match = re.search(r'P\d+_TA\(\d{4}\)\d+', identifier)
    return match.group(0) if match else identifier  # Fallback to full ID if no match

def extract_legal_document_type(title):
    match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+of\s+\d', title, re.IGNORECASE)
    if not match:
        match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+adopted by', title, re.IGNORECASE)
    return match.group(1).strip() if match else "Resolution"  # Default if not found

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%b-%Y")
    except:
        return date_str

# --- Fetch from API ---
def fetch_adopted_documents():
    results = []
    params = {
        "year": YEAR,
        "sitting-date-start": START_DATE,
        "work-type-adopted-texts": "adopted-text",  # Filter for adopted texts
        "format": "all",  # Full details including manifestations (PDF/DOCX)
        "limit": 50,  # Adjust if needed; paginate if >50
        "offset": 0
    }
    headers = {
        "Accept": "application/ld+json",
        "User-Agent": "EP-Scraper/1.0"  # Required for feeds/endpoints
    }

    print("🚀 Fetching adopted texts from API...")
    response = requests.get(f"{API_BASE}/adopted-texts", params=params, headers=headers)
    if response.status_code != 200:
        print(f"❌ API error: {response.status_code} - {response.text}")
        return results

    data = response.json()
    documents = data.get("data", [])

    for doc in documents:
        try:
            title = doc.get("title", {}).get("en", "")  # English title; adjust lang if needed
            published_date = parse_date(doc.get("date", "") or doc.get("sittingDate", ""))
            doc_reference = extract_document_reference(doc.get("identifier", "") or doc.get("docId", ""))
            inter_inst_code = extract_inter_institutional_code(title)
            doc_name = re.sub(r'\s*\d{4}/\d{4}\([A-Z]+\)\s*$', '', title).strip()
            legal_type = extract_legal_document_type(title)
            pdf_link = ""
            docx_link = ""

            # Extract PDF/DOCX from manifestations (if included)
            manifestations = doc.get("manifestation", [])  # Or follow 'url' to fetch details if not in list
            for manif in manifestations:
                manif_type = manif.get("media_type", "").lower()
                manif_url = manif.get("url", "")  # Or 'is_exemplified_by'
                if "pdf" in manif_type:
                    pdf_link = manif_url
                elif "docx" in manif_type or "word" in manif_type:
                    docx_link = manif_url

            # If links not in list, fetch detail endpoint
            if not pdf_link or not docx_link:
                detail_resp = requests.get(f"{API_BASE}/adopted-texts/{doc.get('docId')}", headers=headers)
                if detail_resp.status_code == 200:
                    detail_data = detail_resp.json()
                    # Extract manifestations from detail (similar loop)

            entry = {
                "Source": "Plenary",
                "Inter-institutional code": inter_inst_code,
                "Document reference": doc_reference,
                "Latest EP document name": doc_name,
                "Legal document type": legal_type,
                "Latest EP PDF link": pdf_link,
                "Latest EP Docx link": docx_link,
                "Published Date": published_date,
                "Date when first parsed": datetime.utcnow().strftime("%d-%b-%Y")
            }
            results.append(entry)
        except Exception as e:
            print(f"⚠️ Error processing doc {doc.get('id')}: {e}")

    print(f"✅ Fetched {len(results)} documents")
    return results

if __name__ == "__main__":
    print("="*70)
    print("🇪🇺 European Parliament Document Fetcher (API)")
    print("="*70)
    data = fetch_adopted_documents()
    with open("ep_documents.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Data saved to: ep_documents.json")
