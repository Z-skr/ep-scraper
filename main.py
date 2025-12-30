from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_START = "01/07/2025"
OUTPUT_FILE = "ep_documents.json"

def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # Cliquer sur "More options" si visible
        more_options = page.locator("h4:has-text('More options')")
        if more_options.count() > 0 and more_options.is_visible():
            more_options.click()
            page.wait_for_selector(".expand_collapse_content", state="visible", timeout=15000)

        # Attendre que le champ date soit visible
        start_date_input = page.locator("#refSittingDateStart")
        start_date_input.wait_for(state="visible", timeout=15000)
        start_date_input.fill(DATE_START)

        # Lancer la recherche
        page.locator("#sidesButtonSubmit").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # Pagination et extraction
        while True:
            notices = page.locator("div.notice")
            count = notices.count()
            print(f"📄 Documents sur cette page : {count}")

            for i in range(count):
                notice = notices.nth(i)

                # Titre
                title_elem = notice.locator("p.title a")
                title = title_elem.inner_text().strip() if title_elem.count() > 0 else ""

                # Documents PDF/DOCX/HTML
                doc_links = notice.locator("ul.documents li a")
                for j in range(doc_links.count()):
                    link_elem = doc_links.nth(j)
                    url = link_elem.get_attribute("href")
                    if url and not url.startswith("http"):
                        url = "https://www.europarl.europa.eu" + url
                    results.append({
                        "title": title,
                        "url": url,
                        "scraped_at": datetime.utcnow().isoformat()
                    })

            # Passer à la page suivante
            next_button = page.locator("a:has-text('Next')")
            if next_button.count() > 0 and next_button.is_visible():
                next_button.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
            else:
                break

        browser.close()

    # Sauvegarder JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}, total documents : {len(results)}")


if __name__ == "__main__":
    run()








