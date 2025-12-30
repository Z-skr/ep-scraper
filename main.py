from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_START = "01/07/2025"   # Format DD/MM/YYYY
OUTPUT_FILE = "ep_documents.json"

def run():
    results = []

    with sync_playwright() as p:
        # ✅ Chromium headless sur GitHub Actions
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()

        # 1️⃣ Charger la page
        page.goto(URL, timeout=120000, wait_until="networkidle")

        # 2️⃣ Cliquer sur "More options"
        try:
            page.locator(".js_expand_collapse h4", has_text="More options").click()
            page.wait_for_selector(".expand_collapse_content", state="visible", timeout=15000)
        except:
            print("⚠️ 'More options' non trouvé, continuer...")

        # 3️⃣ Remplir la date de début
        try:
            page.fill("#refSittingDateStart", DATE_START)
        except:
            print("⚠️ Champ date de début non trouvé, continuer...")

        # 4️⃣ Cliquer sur rechercher
        page.locator("#sidesButtonSubmit").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # 5️⃣ Pagination
        while True:
            page.wait_for_timeout(2000)  # Attente pour le rendu
            articles = page.locator("div.notice")
            count = articles.count()
            print(f"📄 Articles trouvés sur cette page : {count}")

            for i in range(count):
                art = articles.nth(i)
                # Titre principal
                title_elem = art.locator("p.title a")
                title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""

                # Documents PDF/DOCX/HTML
                links = art.locator("ul.documents li a")
                for j in range(links.count()):
                    link = links.nth(j)
                    url = link.get_attribute("href")
                    if url and not url.startswith("http"):
                        url = "https://www.europarl.europa.eu" + url
                    results.append({
                        "title": title,
                        "url": url,
                        "scraped_at": datetime.utcnow().isoformat()
                    })

            # 6️⃣ Passer à la page suivante si existe
            next_btn = page.locator("a.next")
            if next_btn.count() > 0 and "disabled" not in next_btn.get_attribute("class"):
                next_btn.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)
            else:
                break

        browser.close()

    # 7️⃣ Sauvegarde JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}, total articles : {len(results)}")

if __name__ == "__main__":
    run()










