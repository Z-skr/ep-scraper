from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
OUTPUT_FILE = "ep_documents.json"


def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 Chargement de la page...")
        page.goto(URL, timeout=120000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Scroll pour forcer le chargement des notices
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        # Vérifier s'il y a des notices
        notice_count = page.locator("div.notice").count()
        if notice_count == 0:
            print("⚠️ Aucun document trouvé, attendre un peu plus...")
            page.wait_for_timeout(5000)
            notice_count = page.locator("div.notice").count()

        print(f"📄 Notices trouvées : {notice_count}")

        # Boucle sur les notices
        for i in range(notice_count):
            notice = page.locator("div.notice").nth(i)
            title_elem = notice.locator("p.title a")
            title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""
            url_elem = title_elem
            url = url_elem.get_attribute("href") if url_elem.count() > 0 else ""

            # Ajouter le domaine si nécessaire
            if url and not url.startswith("http"):
                url = "https://www.europarl.europa.eu" + url

            results.append({
                "title": title,
                "url": url,
                "scraped_at": datetime.utcnow().isoformat()
            })

        browser.close()

    # Sauvegarde JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}, total documents : {len(results)}")


if __name__ == "__main__":
    run()












