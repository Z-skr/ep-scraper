from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import os
import re

URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_START = "01/07/2025"

OUTPUT_FILE = os.path.join(os.getcwd(), "ep_documents.json")

def run():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, timeout=90000)
        page.wait_for_load_state("networkidle")

        try:
            page.locator(".js_expand_collapse h4", has_text="More options").click(timeout=5000)
        except:
            pass

        page.wait_for_timeout(3000)

        try:
            page.fill("#refSittingDateStart", DATE_START)
        except:
            pass

        try:
            page.locator("#sidesButtonSubmit").click()
        except:
            pass

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        while True:
            notices = page.locator(".notice")
            print(f"📄 Articles sur cette page : {notices.count()}")

            for i in range(notices.count()):
                notice = notices.nth(i)

                # 🔹 Title
                title = ""
                title_locator = notice.locator("p.title a")
                if title_locator.count() > 0:
                    title = title_locator.inner_text().strip()

                # 🔹 Inter-institutional code
                inter_code = ""
                details_locator = notice.locator("p.details")
                if details_locator.count() > 0:
                    details_text = details_locator.inner_text()
                    match = re.search(r"\(([^()]+)\)", details_text)
                    if match:
                        inter_code = match.group(1)

                # 🔹 Reference
                reference = ""
                ref_locator = notice.locator("span.reference")
                if ref_locator.count() > 0:
                    reference = ref_locator.inner_text().strip()

                # 🔹 Published Date
                published_date = ""
                date_locator = notice.locator("span.date")
                if date_locator.count() > 0:
                    published_date = date_locator.inner_text().replace("Date :", "").strip()

                # 🔹 Documents
                docs = notice.locator("ul.documents li a")
                for j in range(docs.count()):
                    link = docs.nth(j)
                    url = link.get_attribute("href")

                    if url and not url.startswith("http"):
                        url = "https://www.europarl.europa.eu" + url

                    results.append({
                        "title": title,
                        "inter_institutional_code": inter_code,
                        "reference": reference,
                        "published_date": published_date,
                        "url": url,
                        "scraped_at": datetime.utcnow().isoformat().replace("T", ",T")
                    })

            try:
                next_btn = page.locator("a.next_page")
                if next_btn.is_visible():
                    next_btn.click()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(3000)
                else:
                    break
            except:
                break

        browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}, total documents : {len(results)}")

if __name__ == "__main__":
    run()



