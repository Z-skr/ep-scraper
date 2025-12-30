from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from datetime import datetime
import json
import time
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

        print(f"📡 Chargement de la page: {EP_URL}")
        page.goto(EP_URL, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        # 1️⃣ Vérifier si "Less options" est visible
        print("🔍 Vérification du panneau More options...")
        if not page.query_selector("text=Less options"):
            more_btn = page.query_selector("text=More options")
            if more_btn:
                more_btn.click()
                try:
                    page.wait_for_selector("text=Less options", timeout=15000)
                    print("✅ Panneau More options ouvert")
                except PWTimeoutError:
                    print("⚠️ Timeout en attendant Less options, on continue...")
                time.sleep(2)  # sécurité headless
            else:
                print("⚠️ Bouton More options non trouvé")
        else:
            print("✅ Panneau More options déjà ouvert")

        # 2️⃣ Remplir le champ date "Sittings from"
        print(f"📅 Remplissage du champ date avec: {DATE_FROM}")

        date_input = None
        selectors = [
            "input[type='date']",
            "input[name*='from' i]",
            "label:has-text('Sittings from') + input",
            "#sidesForm input[type='date']"
        ]

        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=15000)
                date_input = page.query_selector(selector)
                if date_input:
                    # Scroll dans le viewport pour headless
                    page.evaluate("element => element.scrollIntoView()", date_input)
                    break
            except PWTimeoutError:
                continue

        if not date_input:
            print("❌ Aucun champ date trouvé, arrêt du scraping.")
            browser.close()
            return results

        try:
            date_input.fill(DATE_FROM)
            print(f"✅ Date remplie: {DATE_FROM}")
        except Exception as e:
            print(f"⚠️ fill() échoué, essai avec JS: {e}")
            try:
                page.evaluate(f"""
                    const input = document.querySelector('input[type="date"]');
                    if (input) {{
                        input.value = '{DATE_FROM}';
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                """)
                print(f"✅ Date remplie via JS: {DATE_FROM}")
            except Exception as e2:
                print(f"❌ Impossible de remplir le champ date: {e2}")
                browser.close()
                return results

        # 3️⃣ Cliquer sur "Search"
        print("🔎 Clic sur le bouton Search...")
        try:
            page.wait_for_selector("button:has-text('Search')", state='visible', timeout=10000)
            search_btn = page.query_selector("button:has-text('Search')")
            if search_btn:
                search_btn.click()
                print("✅ Bouton Search cliqué")
                time.sleep(5)
                page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            print(f"⚠️ Erreur lors du clic sur Search: {e}")

        # 4️⃣ Récupérer les articles
        print("📄 Récupération des articles...")
        try:
            page.wait_for_selector("article", timeout=10000)
        except PWTimeoutError:
            print("⚠️ Aucun article trouvé après timeout")

        articles = page.query_selector_all("article")
        print(f"✅ {len(articles)} articles trouvés")

        for idx, article in enumerate(articles, 1):
            try:
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
                    "Date when first parsed": datetime.utcnow().strftime("%d-%b-%Y"),
                    "Note": "",
                    "New document": "",
                    "Document typology": "",
                    "Typology confidence level": "",
                    "Report summary": ""
                }

                results.append(entry)
                print(f"  [{idx}] {doc_name[:60]}...")

            except Exception as e:
                print(f"⚠️ Erreur lors du traitement de l'article {idx}: {e}")
                continue

        browser.close()
        print(f"\n✅ Scraping terminé: {len(results)} documents extraits")
    return results

if __name__ == "__main__":
    print("=" * 70)
    print("🇪🇺 European Parliament Document Scraper")
    print("=" * 70)

    data = scrape_ep_documents()

    output_file = "ep_documents.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Données sauvegardées dans: {output_file}")
    if data:
        print("\n📊 Aperçu du premier document:")
        print(json.dumps(data[0], ensure_ascii=False, indent=2))
    print("\n✨ Terminé!")
