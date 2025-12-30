from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"

DATE_START = "01/07/2025"   # FORMAT OBLIGATOIRE : DD/MM/YYYY
DATE_END   = "31/12/2025"

OUTPUT_FILE = "ep_documents.json"


def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Charger la page
        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # 2️⃣ Cliquer sur "More options" (HTML que TU as fourni)
        page.locator(".js_expand_collapse h4", has_text="More options").click()

        # 3️⃣ Attendre l’ouverture du bloc
        page.wait_for_selector(".expand_collapse_content", state="visible", timeout=15000)

        # 4️⃣ Remplir les dates
        page.fill("#refSittingDateStart", DATE_START)
        page.fill("#refSittingDateEnd", DATE_END)

        # 5️⃣ Lancer la recherche (✅ CORRECTION ICI)
        page.locator("#sidesButtonSubmit").click()

        # 6️⃣ Attendre les résultats
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # 7️⃣ Extraire les documents
        links = page.locator("a[href*='/doceo/']")
        count = links.count()

        print(f"📄 Documents trouvés : {count}")

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

        browser.close()

    # 8️⃣ Sauvegarde JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}")


if __name__ == "__main__":
    run()

