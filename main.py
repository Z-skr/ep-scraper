from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime
import json
import time

EP_URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_FROM = "2025-07-01"  # YYYY-MM-DD

def scrape_ep_documents():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(EP_URL, timeout=60000)

        # 1️⃣ Cliquer sur "More options" si visible
        try:
            more_btn = page.query_selector("text=More options")
            if more_btn:
                more_btn.click()
                # attendre que le bouton devienne "Less options"
                page.wait_for_selector("text=Less options", timeout=60000)
        except TimeoutError:
            print("Bouton More options pas trouvé ou déjà ouvert.")

        # 2️⃣ Attendre que le champ "Settings from" soit visible
        page.wait_for_selector("input[type='date']", timeout=60000)
        date_inputs = page.query_selector_all("input[type='date']")
        if date_inputs:
            date_inputs[0].fill(DATE_FROM)
        else:
            print("Champ date non trouvé.")
            return results

        # 3️⃣ Cliquer sur "Search" et attendre que les résultats se mettent à jour
        page.click("button:has-text('Search')")
        # attendre un petit délai pour que le JS charge les résultats
        time.sleep(3)

        # 4️⃣ Récupérer les articles
        articles = page.query_selector_all("article")

        for article in articles:
            link = article.query_selector("a")
            if not link:
                continue

            title = link.inner_text().strip()
            href = link.get_attribute("href")
            if not href:
                continue

            url = href if href.startswith("http") else "https://www.europarl.europa.eu" + href

            results.append({
                "title": title,
                "url": url,
                "source": "European Parliament",
                "parsed_at": datetime.utcnow().isoformat()
            })

        browser.close()

    return results


if __name__ == "__main__":
    data = scrape_ep_documents()

    with open("ep_documents.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(json.dumps(data, ensure_ascii=False, indent=2))


