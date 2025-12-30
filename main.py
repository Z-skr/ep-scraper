from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
OUTPUT_FILE = "ep_documents.json"

def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        print("🌐 Chargement de la page...")
        page.goto(URL, timeout=120000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)  # laisser le JS charger

        # Boucle sur les pages de résultats (pagination)
        while True:
            print("📄 Extraction des documents de la page...")

            notices = page.locator("div.notice")
            count = notices.count()
            for i in range(count):
                notice = notices.nth(i)
                
                # Titre principal
                title_elem = notice.locator("p.title a")
                title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""
                
                # Description / details
                details_elem = notice.locator("p.details")
                details = details_elem.inner_text().strip() if details_elem.count() > 0 else ""

                # Documents PDF / DOCX
                docs = []
                for doc_link in notice.locator("ul.documents li a").all():
                    doc_url = doc_link.get_attribute("href")
                    if doc_url and not doc_url.startswith("http"):
                        doc_url = "https://www.europarl.europa.eu" + doc_url
                    docs.append(doc_url)

                # URL HTML
                html_url = title_elem.get_attribute("href") if title_elem.count() > 0 else ""
                if html_url and not html_url.startswith("http"):
                    html_url = "https://www.europarl.europa.eu" + html_url

                # Ajouter à la liste
                results.append({
                    "title": title,
                    "details": details,
                    "url_html": html_url,
                    "documents": docs,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            # Pagination : bouton "Next" s'il existe
            next_buttons = page.locator("a.next")
            if next_buttons.count() > 0:
                print("➡️ Passage à la page suivante...")
                next_buttons.first.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
            else:
                print("✅ Dernière page atteinte.")
                break

        browser.close()

    # Sauvegarde JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"🎯 Fichier généré : {OUTPUT_FILE}")
    print(f"📄 Total documents : {len(results)}")

if __name__ == "__main__":
    run()











