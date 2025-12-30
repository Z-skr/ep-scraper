from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from datetime import datetime
import json
import time
import re
import os

EP_URL = "https://www.europarl.europa.eu/plenary/en/texts-adopted.html"
DATE_FROM = "2025-07-01"  # YYYY-MM-DD

# Créer un dossier pour debug
os.makedirs("debug", exist_ok=True)

# --- Fonctions d'extraction --- (inchangées)
def extract_inter_institutional_code(title):
    match = re.search(r'\b(\d{4}/\d{4}\([A-Z]+\))\b', title)
    return match.group(1) if match else ""

def extract_document_reference(text):
    match = re.search(r'P\d+_TA\(\d{4}\)\d+', text)
    return match.group(0) if match else ""

def extract_legal_document_type(title):
    match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+of\s+\d', title, re.IGNORECASE)
    if not match:
        match = re.search(r'European Parliament\s+(\w+(?:\s+\w+)*?)\s+adopted by', title, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d-%b-%Y").strftime("%d-%b-%Y")
    except:
        return date_str

# --- Scraper ---
def scrape_ep_documents():
    results = []
    with sync_playwright() as p:
        print("🚀 Lancement du navigateur...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(EP_URL, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        page.screenshot(path="debug/01_initial_page.png")
        print("📸 Screenshot: page initiale")

        # --- Ouvrir More options ---
        try:
            more_btn = page.query_selector("text=/More options/i")
            if more_btn.is_visible():
                more_btn.scroll_into_view_if_needed()
                more_btn.click()
                print("👉 More options cliqué")
                page.wait_for_selector("text=/Less options/i", timeout=10000)
            page.screenshot(path="debug/02_after_more_options.png")
            print("📸 Screenshot: après More options")
        except Exception as e:
            print(f"⚠️ More options non trouvé ou déjà ouvert : {e}")

        # --- Remplir date ---
        try:
            date_input = page.query_selector("input[type='date'] >> nth=0")  # Premier input date
            if not date_input:
                date_input = page.query_selector("label:has-text('Sittings from') ~ input")
            if date_input:
                date_input.fill("")
                date_input.fill(DATE_FROM)
                date_input.press("Enter")
                print(f"📅 Date remplie: {DATE_FROM}")
            else:
                print("❌ Input date non trouvé")
            page.screenshot(path="debug/03_after_date_fill.png")
        except Exception as e:
            print(f"⚠️ Erreur remplissage date : {e}")

        time.sleep(2)

        # --- Cliquer Search ---
        try:
            search_btn = page.query_selector("button:has-text('SEARCH')")  # Tout en majuscules sur le site
            if not search_btn:
                search_btn = page.query_selector("form button[type='submit']")
            if search_btn:
                search_btn.click()
                print("👉 Bouton SEARCH cliqué")
            else:
                print("❌ Bouton SEARCH non trouvé")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(5)  # Attente supplémentaire pour AJAX
            page.screenshot(path="debug/04_after_search.png")
            print("📸 Screenshot: après recherche (clé pour debug)")
        except Exception as e:
            print(f"⚠️ Erreur clic search : {e}")

        # --- Sauvegarder HTML complet pour inspection ---
        with open("debug/page_after_search.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("💾 HTML de la page après recherche sauvegardé")

        # --- Essayer plusieurs selectors pour les items ---
        possible_selectors = [
            "div.ep-a_searchResult",       # Très probable
            "div.erpl_search-result-item",
            "div.ep_search-result-item",
            "article",
            "div[class*='search-result' i]",
            "div[class*='document' i]"
        ]

        articles = []
        for sel in possible_selectors:
            articles = page.query_selector_all(sel)
            if articles:
                print(f"✅ Items trouvés avec selector: {sel} ({len(articles)} items)")
                break
        else:
            print("❌ Aucun item trouvé avec tous les selectors testés")

        # Extraction (inchangée, mais avec plus de logs)
        for idx, article in enumerate(articles, 1):
            try:
                # ... (ton code d'extraction existant ici)
                # Je le garde identique pour ne pas tout réécrire, mais ajoute des prints si besoin
                # ...
                results.append(entry)
                print(f"✅ Document {idx} extrait")
            except Exception as e:
                print(f"⚠️ Erreur extraction item {idx}: {e}")

        browser.close()

    return results

if __name__ == "__main__":
    data = scrape_ep_documents()
    with open("ep_documents.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(data)} documents extraits et sauvegardés")
