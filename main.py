from playwright.sync_api import sync_playwright
from datetime import datetime
import json
import re

EP_URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_FROM = "2025-07-01"  # YYYY-MM-DD

def extract_inter_institutional_code(title):
    match = re.search(r'\b(\d{4}/\d{4}\([A-Z]+\))\b', title)
    return match.group(1) if match else ""

def extract_document_reference(text):
    match = re.search(r'P\d+_TA\(\d{4}\)\d+', text)
    return match.group(0) if match else ""

def extract_legal_document_type(title):
    match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+of\s+\d', title, re.IGNORECASE)
    if not match:
        match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+adopted by', title, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d-%b-%Y").strftime("%d-%b-%Y")
    except:
        return date_str

def scrape_ep_documents():
    results = []

    with sync_playwright() as p:
        print("🚀 Lancement du navigateur...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(EP_URL, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)

        # Ouvrir "More options" si présent
        more_btn = page.query_selector("text=More options")
        if more_btn:
            more_btn.click()
            page.wait_for_selector("text=Less options", timeout=10000)

        # Remplir le champ date si présent
        date_input = page.query_selector("input[type='date']")
        if date_input:
            date_input.fill(DATE_FROM)

        # Cliquer sur Search
        search_btn = page.query_selector("button:has-text('Search')")
        if search_btn:
            search_btn.click()
            page.wait_for_load_state("networkidle", timeout=15000)

        # Récupérer tous les articles
        items = page.query_selector_all("ul.results li")  # adapte selon inspection du site
        print(f"✅ {len(items)} éléments trouvés")

        for idx, item in enumerate(items, 1):
            try:
                title_elem = item.query_selector("a")
                title = title_elem.inner_text().strip() if title_elem else ""
                href = title_elem.get_attribute("href") if title_elem else ""
                full_url = href if href.startswith("http") else "https://www.europarl.europa.eu" + href

                text_content = item.inner_text()

                inter_inst_code = extract_inter_institutional_code(title)
                doc_reference = extract_document_reference(text_content)
                legal_type = extract_legal_document_type(title)

                # Extraire date
                date_match = re.search(r'(\d{2}-[A-Za-z]{3}-\d{4})', text_content)
                published_date = parse_date(date_match.group(1)) if date_match else ""

                # Extraire PDF / DOCX si présent
                pdf_link = ""
                docx_link = ""
                links = item.query_selector_all("a")
                for link in links:
                    link_href = link.get_attribute("href")
                    link_text = link.inner_text().strip().lower()
                    if link_href:
                        full_link = link_href if link_href.startswith("http") else "https://www.europarl.europa.eu" + link_href
                        if "pdf" in link_href.lower() or "pdf" in link_text:
                            pdf_link = full_link
                        elif "doc" in link_href.lower() or "word" in link_text:
                            docx_link = full_link

                results.append({
                    "Source": "Plenary",
                    "Inter-institutional code": inter_inst_code,
                    "Document reference": doc_reference,
                    "Latest EP document name": title,
                    "Legal document type": legal_type,
                    "Latest EP PDF link": pdf_link,
                    "Latest EP Docx link": docx_link,
                    "Published Date": published_date,
                    "Date when first parsed": datetime.utcnow().strftime("%d-%b-%Y")
                })
            except Exception as e:
                print(f"⚠️ Erreur élément {idx}: {e}")
                continue

        browser.close()
    print(f"\n✅ Scraping terminé: {len(results)} documents extraits")
    return results

if __name__ == "__main__":
    print("="*70)
    print("🇪🇺 European Parliament Document Scraper")
    print("="*70)
    data = scrape_ep_documents()
    with open("ep_documents.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Données sauvegardées dans: ep_documents.json")


