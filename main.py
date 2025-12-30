from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"

DATE_START = "01/07/2025"  # FORMAT DD/MM/YYYY
DATE_END = "31/12/2025"

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

        # 3️⃣ Remplir les dates
        page.fill("#refSittingDateStart", DATE_START)
        page.fill("#refSittingDateEnd", DATE_END)

        # 4️⃣ Lancer la recherche
        page.locator("#sidesButtonSubmit").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        page_number = 1
        while True:
            print(f"🔹 Extraction page {page_number}")

            # 5️⃣ Extraire les documents sur la page actuelle
            links = page.locator("a[href*='/doceo/']")
            count = links.count()
            print(f"📄 Documents trouvés sur cette page : {count}")

            for i in range(count):
                link = links.nth(i)
                title = link.inner_text().strip()
                url = link.get_attribute("href")

                if url and not url.startswith("http"):
                    url = "https://www.europarl.europa.eu" + url

                results.append({
                    "title": title,
                    "url": url,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            # 6️⃣ Vérifier si un bouton "Next" existe
            next_button = page.locator("a.pagination-next")
            if next_button.count() == 0 or "disabled" in next_button.get_attribute("class"):
                break  # plus de pages
            else:
                next_button.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
                page_number += 1

        browser.close()

    # 7️⃣ Sauvegarde JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}")
    print(f"🔹 Total documents : {len(results)}")

if __name__ == "__main__":
    run()




