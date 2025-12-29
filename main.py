import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import re

EP_URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
SITTINGS_FROM = "01/07/2025"

def scrape_ep_documents():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(EP_URL, timeout=60000)
        page.click("text=More Options")
        page.fill("input[name='sittingsFrom']", SITTINGS_FROM)
        page.click("button:has-text('Apply')")
        page.wait_for_load_state("networkidle")

        documents = page.query_selector_all(".ep-documents__result")  # à ajuster selon le site
        for doc in documents:
            try:
                title_el = doc.query_selector("h3")
                title = title_el.inner_text().strip() if title_el else ""
                match_code = re.search(r"\((\d{4}/\d+\([A-Z]+\))\)", title)
                inter_code = match_code.group(1) if match_code else ""
                ref_el = doc.query_selector(".document-ref")
                document_ref = ref_el.inner_text().strip() if ref_el else ""
                pdf_el = doc.query_selector("a.pdf-icon")
                pdf_link = pdf_el.get_attribute("href") if pdf_el else ""
                docx_el = doc.query_selector("a.word-icon")
                docx_link = docx_el.get_attribute("href") if docx_el else ""
                date_el = doc.query_selector(".published-date")
                published_date = date_el.inner_text().strip() if date_el else ""
                results.append({
                    "title": title,
                    "inter_code": inter_code,
                    "document_ref": document_ref,
                    "pdf": pdf_link,
                    "docx": docx_link,
                    "published_date": published_date
                })
            except:
                pass
        browser.close()
    return results

if __name__ == "__main__":
    data = scrape_ep_documents()
    # Écriture dans un fichier JSON dans le repo (optionnel)
    with open("ep_documents.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Affichage pour GitHub Actions / n8n
    print(json.dumps(data, ensure_ascii=False))
