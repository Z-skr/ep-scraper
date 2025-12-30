import requests
from datetime import datetime
import json
import re

API_BASE = "https://data.europarl.europa.eu/api/v2"
START_DATE = "2025-07-01"
YEAR = "2025"

# --- Fonctions d'extraction ---
def extract_inter_institutional_code(title):
    match = re.search(r'\b(\d{4}/\d{4}\([A-Z]+\))\b', title)
    return match.group(1) if match else ""

def extract_document_reference(identifier):
    match = re.search(r'P\d+_TA\(\d{4}\)\d+', identifier)
    return match.group(0) if match else identifier

def extract_legal_document_type(title):
    match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+of\s+\d', title, re.IGNORECASE)
    if not match:
        match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+adopted by', title, re.IGNORECASE)
    return match.group(1).strip() if match else "Resolution"

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%b-%Y")
    except:
        return date_str

# --- Fetch documents safely ---
def fetch_adopted_documents():
    results = []
    params = {
        "year": YEAR,
        "sitting-date-start": START_DATE,
        "work-type-adopted-texts": "adopted-text",
        "format": "all",
        "limit": 50,
        "offset": 0
    }
    headers = {
        "Accept": "application/json",  # Changed from ld+json
        "User-Agent": "EP-Scraper/1.0"
    }

    print("🚀 Fetching adopted texts from API...")
    response = requests.get(f"{API_BASE}/adopted-texts", params=params, headers=headers)

    if response.status_code != 200:
        print(f"❌ API error: {response.status_code}")
        print("Response preview:", response.text[:500])
        return results

    try:
        data = response.json()
    except ValueError as e:
        print("❌ Failed to parse JSON:", e)
        print("Response preview:", response.text[:500])
        return results

    documents = data.get("data", [])
    if not documents:
        print("⚠️ No documents returned by API.")
        return results

    for doc in documents:
        try:
            title = doc.get("title", {}).get("en", "")
            published_date = parse_date(doc.get("date", "") or doc.get("sittingDate", ""))
            doc_reference = extract_document_reference(doc.get("identifier", "") or doc.get("docId", ""))
            inter_inst_code = extract_inter_institutional_code(title)
            doc_name = re.sub(r'\s*\d{4}/\d{4}\([A-Z]+\)\s*$', '', title).strip()
            legal_type = extract_legal_document_type(title)
            pdf_link = ""
            docx_link = ""

            manifestations = doc.get("manifestation", [])
            for manif in manifestations:
                manif_type = manif.get("media_type", "").lower()
                manif_url = manif.get("url", "")
                if "pdf" in manif_type:
                    pdf_link = manif_url
                elif "docx" in manif_type or "word" in manif_type:
                    docx_link = manif_url

            # Optional: fetch details if no links found
            if not pdf_link or not docx_link:
                detail_resp = requests.get(f"{API_BASE}/adopted-texts/{doc.get('docId')}", headers=headers)
                if detail_resp.status_code == 200:
                    try:
                        detail_data = detail_resp.json()
                        manif_detail = detail_data.get("manifestation", [])
                        for manif in manif_detail:
                            manif_type = manif.get("media_type", "").lower()
                            manif_url = manif.get("url", "")
                            if "pdf" in manif_type and not pdf_link:
                                pdf_link = manif_url
                            elif ("docx" in manif_type or "word" in manif_type) and not docx_link:
                                docx_link = manif_url
                    except ValueError:
                        pass

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
