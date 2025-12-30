import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"

# Fonction pour récupérer les documents d'une page
def get_documents_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    notices = soup.select(".listcontent .notice")
    docs = []
    for notice in notices:
        title_tag = notice.select_one("p.title a")
        pdf_tag = notice.select_one("ul.documents .link_pdf")
        docx_tag = notice.select_one("ul.documents .link_doc")
        details_tag = notice.select_one("p.details")
        date_tag = notice.select_one(".date_reference .date")
        ref_tag = notice.select_one(".date_reference .reference")
        
        doc = {
            "title": title_tag.get_text(strip=True) if title_tag else None,
            "link_html": title_tag['href'] if title_tag else None,
            "link_pdf": pdf_tag['href'] if pdf_tag else None,
            "link_docx": docx_tag['href'] if docx_tag else None,
            "details": details_tag.get_text(strip=True) if details_tag else None,
            "date": date_tag.get_text(strip=True) if date_tag else None,
            "reference": ref_tag.get_text(strip=True) if ref_tag else None,
        }
        docs.append(doc)
    return docs

# Fonction principale pour parcourir les pages
def scrape_all_documents():
    all_docs = []
    page = 0
    while True:
        # Requête GET avec paramètre de pagination
        response = requests.get(BASE_URL, params={"action": page})
        if response.status_code != 200:
            print(f"Erreur pour la page {page}")
            break
        docs = get_documents_from_html(response.text)
        if not docs:
            break  # Plus de résultats
        all_docs.extend(docs)
        print(f"Page {page + 1} récupérée, {len(docs)} documents")
        page += 1
    return all_docs

# Exécution
documents = scrape_all_documents()
print(f"Total documents récupérés: {len(documents)}")

# Exemple d'affichage
for d in documents[:5]:  # afficher les 5 premiers
    print(d)


