from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"

DATE_START = "01/07/2025"   # FORMAT OBLIGATOIRE : DD/MM/YYYY
OUTPUT_FILE = "ep_documents.json"


def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Charger la page
        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # 2️⃣ Cliquer sur "More options"
        page.locator(".js_expand_collapse h4", has_text="More options").click()
        page.wait_for_selector(".expand_collapse_content", state="visible", timeout=15000)

        # 3️⃣ Remplir la date de début
        page.fill("#refSittingDateStart", DATE_START)
        page.fill("#refSittingDateEnd", "")  # laisser vide pour toujours jusqu'à aujourd'hui

        # 4️⃣ Lancer la recherche
        page.locator("#sidesButtonSubmit").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # 5️⃣ Pagination et extraction
        while True:
            articles = page.locator("div.notice")
            count = articles.count()
            print(f"📄 Articles sur cette page : {count}")

            for i in range(count):
                article = articles.nth(i)

                # Titre
                title = article.locator("p.title a").inner_text().strip()

                # Description
                description = article.locator("p.details").inner_text().strip()

                # Date et référence
                date = article.locator("div.date_reference span.date").inner_text().strip()
                reference = article.locator("div.date_reference span.reference").inner_text().strip()

                # Documents PDF / DOCX
                doc_links = []
                for link in article.locator("ul.documents li a").all():
                    url = link.get_attribute("href")
                    if url and not url.startswith("http"):
                        url = "https://www.europarl.europa.eu" + url
                    doc_links.append(url)

                results.append({
                    "title": title,
                    "description": description,
                    "date": date,
                    "reference": reference,
                    "documents": doc_links,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            # Pagination : next page
            next_button = page.locator("a[title='Next']")
            if next_button.is_visible():
                next_button.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
            else:
                break

        browser.close()

    # 6️⃣ Sauvegarde JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}")


if __name__ == "__main__":
    run()






