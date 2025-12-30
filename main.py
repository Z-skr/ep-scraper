from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from datetime import datetime
import json
import time
import re

EP_URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_FROM = "2025-07-01"  # YYYY-MM-DD

# --- Fonctions d'extraction --- (unchanged, keeping your original)

# --- Scraper ---
def scrape_ep_documents():
    results = []
    with sync_playwright() as p:
        print("🚀 Lancement du navigateur...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"📡 Chargement de la page: {EP_URL}")
        page.goto(EP_URL, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        # --- Ouvrir More options de façon robuste ---
        try:
            page.wait_for_selector("text=More options", timeout=10000)
            more_btn = page.query_selector("text=More options")
            if more_btn:
                page.evaluate("element => element.scrollIntoView()", more_btn)
                page.wait_for_selector("text=More options", state="visible", timeout=10000)
                more_btn.click()
                print("👉 Cliqué sur More options")
                page.wait_for_selector("text=Less options", timeout=10000)
                print("✅ Panneau More options ouvert")
            else:
                print("ℹ️ Bouton More options non trouvé ou déjà ouvert")
        except Exception as e:
            print(f"⚠️ Impossible de cliquer More options (ignoré): {e}")
        time.sleep(1)

        # --- Remplir le champ date ---
        print(f"📅 Remplissage du champ date avec: {DATE_FROM}")
        date_input = None
        selectors = ["input[type='date']", "input[name*='from' i]", "label:has-text('Sittings from') + input", "#sidesForm input[type='date']"]
        for selector in selectors:
            date_input = page.query_selector(selector)
            if date_input:
                print(f"✅ Champ date trouvé: {selector}")
                break
        if not date_input:
            print("❌ Aucun champ date trouvé")
            browser.close()
            return results
        try:
            date_input.fill(DATE_FROM)
        except:
            page.evaluate(f"""
                const input = document.query_selector('{selectors[-1]}');  # Use the last selector as fallback
                if (input) {{
                    input.value = '{DATE_FROM}';
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)
        time.sleep(1)  # Extra wait after setting date

        # --- Cliquer sur Search (more specific selector) ---
        try:
            search_btn = page.query_selector("#sidesForm button:has-text('Search')")
            if search_btn:
                search_btn.click()
                print("👉 Cliqué sur Search")
                time.sleep(2)  # Initial short wait
                page.wait_for_load_state("networkidle", timeout=15000)
                # Wait for results header to confirm load
                page.wait_for_selector("div:has-text('Result(s)')", timeout=30000)
                print("✅ Résultats chargés (en-tête 'Result(s)' détecté)")
                time.sleep(3)  # Extra wait for full JS render
            else:
                print("❌ Bouton Search non trouvé dans #sidesForm")
        except PWTimeoutError:
            print("⚠️ Timeout en attendant les résultats - la recherche n'a pas déclenché ou pas chargé")
            browser.close()
            return results

        # --- Récupérer articles (updated selector) ---
        print("📄 Récupération des articles...")
        articles = page.query_selector_all("div.erpl_document-wrap")  # Main fix: change to this
        # Alternative if above gets 0: articles = page.query_selector_all("div.erpl_search-result-item")
        print(f"✅ {len(articles)} articles trouvés")

        for idx, article in enumerate(articles, 1):
            try:
                # Your extraction logic (unchanged) - it should work as long as 'article' is the container div
                title_elem = article.query_selector("a")
                if not title_elem:
                    continue
                bold_title = title_elem.inner_text().strip()
                href = title_elem.get_attribute("href")
                if not href:
                    continue
                pdf_url = href if href.startswith("http") else "https://www.europarl.europa.eu" + href
                article_text = article.inner_text()
                full_title_lines = article_text.split('\n')
                full_title = ""
                for line in full_title_lines[1:]:
                    if line.strip() and not line.startswith('P10_TA'):
                        full_title = line.strip()
                        break
                inter_inst_code = extract_inter_institutional_code(full_title)
                doc_name = re.sub(r'\s*\d{4}/\d{4}\([A-Z]+\)\s*$', '', full_title).strip()
                legal_type = extract_legal_document_type(full_title)
                doc_reference = extract_document_reference(article_text)
                date_match = re.search(r'(\d{2}-[A-Za-z]{3}-\d{4})', article_text)
                published_date = parse_date(date_match.group(1)) if date_match else ""
                pdf_link = ""
                docx_link = ""
                links = article.query_selector_all("a")
                for link in links:
                    link_href = link.get_attribute("href")
                    link_text = link.inner_text().strip().lower()
                    if link_href:
                        full_link = link_href if link_href.startswith("http") else "https://www.europarl.europa.eu" + link_href
                        if "pdf" in link_href.lower() or "pdf" in link_text:
                            pdf_link = full_link
                        elif "doc" in link_href.lower() or "word" in link_text or link_text == "w":
                            docx_link = full_link
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
                print(f"⚠️ Erreur article {idx}: {e}")
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
