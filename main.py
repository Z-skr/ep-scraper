from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_START = "01/07/2025"   # Format obligatoire : DD/MM/YYYY
OUTPUT_FILE = "ep_documents.json"

def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Charger la page
        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # 2️⃣ Cliquer sur "More options" si présent
        try:
            page.locator(".js_expand_collapse h4", has_text="More options").click(timeout=5000)
        except:
            print("⚠️ 'More options' non trouvé, continuer...")

        # 3️⃣ Attendre l’ouverture du bloc
        page.wait_for_selector(".expand_collapse_content", state="visible", timeout=10000)

        # 4️⃣ Remplir uniquement la date de début
        try:
            page.fill("#refSittingDateStart", DATE_START)
        except:
            print("⚠️ Champ date de début non trouvé, continuer...")

        # 5️⃣ Lancer la recherche
        try:
            page.locator("#sidesButtonSubmit").click()
        except:
            print("⚠️ Bouton Submit non trouvé, continuer...")

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # 6️⃣ Pagination
        while True:
            # Extraire les articles de la page
            notices = page.locator(".notice")
            count = notices.count()
            print(f"📄 Articles sur la page : {count}")

            for i in range(count):
                notice = notices.nth(i)
                # Titre principal
                title_locator = notice.locator("p.title a")
                title = title_locator.inner_text().strip() if title_locator.count() > 0 else ""
                
                # Tous les documents
                docs = notice.locator("ul.documents li a")
                for j in range(docs.count()):
                    link = docs.nth(j)
                    url = link.get_attribute("href")
                    if url and not url.startswith("http"):
                        url = "https://www.europarl.europa.eu" + url
                    results.append({
                        "title": title,
                        "url": url,
                        "scraped_at": datetime.utcnow().isoformat()
                    })

            # Vérifier s’il y a une page suivante
            try:
                next_btn = page.locator("a.next")
                if next_btn.is_visible():
                    next_btn.click()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(3000)
                else:
                    break
            except:
                break

        browser.close()

    # 7️⃣ Sauvegarder JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}, total documents : {len(results)}")

if __name__ == "__main__":
    run()













