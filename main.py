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

        # 1️⃣ Charger la page
        page.goto(URL, timeout=90000)
        page.wait_for_load_state("networkidle")

        # 2️⃣ More options
        try:
            page.locator(".js_expand_collapse h4", has_text="More options").click(timeout=5000)
        except:
            print("⚠️ 'More options' non trouvé")

        page.wait_for_timeout(3000)

        # 3️⃣ Date start
        try:
            page.fill("#refSittingDateStart", DATE_START)
        except:
            print("⚠️ Champ date non trouvé")

        # 4️⃣ Search
        try:
            page.locator("#sidesButtonSubmit").click()
        except:
            print("⚠️ Bouton search non trouvé")

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # 5️⃣ Pagination
        while True:
            notices = page.locator(".notice")
            print(f"📄 Articles sur la page : {notices.count()}")

            for i in range(notices.count()):
                notice = notices.nth(i)

                # Title
                title = ""
                title_loc = notice.locator("p.title a")
                if title_loc.count() > 0:
                    title = title_loc.inner_text().strip()

                # Details text
                details_text = ""
                details_loc = notice.locator("p.details")
                if details_loc.count() > 0:
                    details_text = details_loc.inner_text().strip()

                # ✅ Legal document type
                legal_type = ""
                match_type = re.search(
                    r"European Parliament\s+(.*?)\s+of\s+\d{1,2}\s+\w+\s+\d{4}",
                    details_text,
                    re.IGNORECASE
                )
                if match_type:
                    legal_type = match_type.group(1).capitalize()

                # ✅ Inter-institutional code
                inter_code = ""
                match_code = re.search(r"\((\d{4}/\d+\([A-Z]+\))\)", details_text)
                if match_code:
                    inter_code = match_code.group(1)

                # ✅ Published date
                published_date = ""
                date_loc = notice.locator("span.date")
                if date_loc.count() > 0:
                    published_date = date_loc.inner_text().replace("Date :", "").strip()

                # ✅ Reference
                reference = ""
                ref_loc = notice.locator("span.reference")
                if ref_loc.count() > 0:
                    reference = ref_loc.inner_text().strip()

                # ✅ Documents (PDF / DOCX)
                pdf_url = ""
                docx_url = ""
                docs = notice.locator("ul.documents li a")
                for j in range(docs.count()):
                    link = docs.nth(j)
                    href = link.get_attribute("href")
                    if href and not href.startswith("http"):
                        href = "https://www.europarl.europa.eu" + href

                    if href.endswith(".pdf"):
                        pdf_url = href
                    elif href.endswith(".docx"):
                        docx_url = href

                # Scraped timestamp
                scraped_at = datetime.utcnow().isoformat().replace("T", ",T")

                # Append result
                results.append({
                    "title": title,
                    "legal_document_type": legal_type,
                    "inter_institutional_code": inter_code,
                    "reference": reference,
                    "published_date": published_date,
                    "latest_ep_pdf_link": pdf_url,
                    "latest_ep_docx_link": docx_url,
                    "scraped_at": scraped_at
                })

            # Next page
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

    # 6️⃣ Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Fichier généré : {OUTPUT_FILE}")
    print(f"📦 Total documents : {len(results)}")

if __name__ == "__main__":
    run()





