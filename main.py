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
        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # Cliquer sur "More options" si présent
        more_options = page.locator(".js_expand_collapse h4", has_text="More options")
        if more_options.count() > 0:
            more_options.first.click()
            page.wait_for_selector(".expand_collapse_content", state="visible", timeout=15000)

        # Pagination
        while True:
            # Extraire tous les blocs de notice
            notices = page.locator("div.notice")
            count = notices.count()
            print(f"📄 Notices trouvées sur la page : {count}")

            for i in range(count):
                notice = notices.nth(i)
                # Titre
                title_elem = notice.locator("p.title a")
                title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""

                # Documents
                links = notice.locator("ul.documents li a")
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

            # Vérifier s’il y a un bouton "Next"
            next_button = page.locator("a[title='Next page']")
            if next_button.count() > 0 and next_button.first.is_enabled():
                next_button.first.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)  # petit délai pour que les notices s'affichent
            else:
                break

        browser.close()

    # Sauvegarde JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}, total documents : {len(results)}")


if __name__ == "__main__":
    run()









