import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

EP_URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_FROM = datetime.strptime("01/07/2025", "%d/%m/%Y")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (EP Scraper)"
}

def scrape_ep_documents():
    response = requests.get(EP_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for item in soup.select("div.ep-a_text"):
        title = item.get_text(strip=True)
        link = item.find("a")

        if not link:
            continue

        url = "https://www.europarl.europa.eu" + link["href"]

        results.append({
            "title": title,
            "url": url,
            "source": "European Parliament",
            "parsed_at": datetime.utcnow().isoformat()
        })

    return results

if __name__ == "__main__":
    data = scrape_ep_documents()

    with open("ep_documents.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(json.dumps(data, ensure_ascii=False))
