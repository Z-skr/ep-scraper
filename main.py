from playwright.sync_api import sync_playwright
import json
from datetime import datetime

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"

DATE_START = "01/07/2025"
DATE_END   = "31/12/2025"

OUTPUT_FILE = "ep_documents.json"

def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # More options
        page.locator(".js_expand_collapse h4", has_text="More options").click()
        page.wait_for_selector(".expand_collapse_content", state="visible")
        page.fill("#refSittingDateStart", DATE_START)
        page.fill("#refSittingDateEnd", DATE_END)
        page.locator("#sidesButtonSubmit").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        page_number = 1
        while True:
            print(f"🔹 Extraction page {page_number}")
            articles = page.locator("div.notice")
            count = articles.count()
            print(f"📄 Articles trouvés : {count}")

            for i in range(count):
                article = articles.nth(i)
                title_element = article.locator("p.title a")
                title = title_element.inner_text().strip()
                url = title_element.get_attribute("href")

                # Récupérer les fichiers PDF/DOCX
                attachments = []
                doc_links = article.locator("ul.documents li a")
                for j in range(doc_links.count()):
                    doc = doc_links.nth(j)
                    attachments.append(doc.get_attribute("href"))

                results.append({
                    "title": title,
                    "url": url,
                    "attachments": attachments,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            # Pagination
            next_button = page.locator("a.pagination-next")
            if next_button.count() == 0 or "disabled" in next_button.get_attribute("class"):
                break
            else:
                next_button.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
                page_number += 1

        browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}")
    print(f"🔹 Total articles : {len(results)}")

if __name__ == "__main__":
    run()





