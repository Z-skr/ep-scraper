import json
import time
from playwright.sync_api import sync_playwright

# URL des textes adoptés
URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"

def scrape_ep_documents():
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)

        # Si le site a un bouton "More options" pour filtrer par date
        try:
            more_btn = page.query_selector("button[aria-label='More options']")
            if more_btn:
                more_btn.click()
                time.sleep(1)  # attendre que les filtres JS apparaissent
        except:
            pass

        # Sélection de tous les documents
        notices = page.query_selector_all(".notice")  # adapte le sélecteur si nécessaire
        for notice in notices:
            title_elem = notice.query_selector(".title a")
            if title_elem:
                title = title_elem.inner_text().strip()
                link = title_elem.get_attribute("href")
                date_elem = notice.query_selector(".date")
                date = date_elem.inner_text().strip() if date_elem else ""
                data.append({
                    "title": title,
                    "link": link,
                    "date": date
                })

        browser.close()

    return data

if __name__ == "__main__":
    documents = scrape_ep_documents()

    # Sauvegarde JSON
    with open("ep_documents.json", "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"{len(documents)} documents scraped and saved to ep_documents.json")



