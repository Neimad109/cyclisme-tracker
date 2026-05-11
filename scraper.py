"""
Scraper ProCyclingStats — Ex-Arkéa Tracker 2026
Tourne chaque soir à 19h via GitHub Actions.
Met à jour data/results.json avec les derniers résultats.
"""

import json
import re
import time
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

RIDERS = [
    {"id": "vauquelin",    "name": "Kévin Vauquelin",     "pcs": "kevin-vauquelin",           "nat": "🇫🇷", "team": "INEOS Grenadiers"},
    {"id": "costiou",      "name": "Ewen Costiou",         "pcs": "ewen-costiou",              "nat": "🇫🇷", "team": "Groupama-FDJ United"},
    {"id": "mozzato",      "name": "Luca Mozzato",         "pcs": "luca-mozzato",              "nat": "🇮🇹", "team": "Tudor Pro Cycling"},
    {"id": "biermans",     "name": "Jenthe Biermans",      "pcs": "jenthe-biermans",           "nat": "🇧🇪", "team": "Cofidis"},
    {"id": "senechal",     "name": "Florian Sénéchal",     "pcs": "florian-senechal",          "nat": "🇫🇷", "team": "Alpecin-Premier Tech"},
    {"id": "venturini",    "name": "Clément Venturini",    "pcs": "clement-venturini",         "nat": "🇫🇷", "team": "Unibet Rose Rockets"},
    {"id": "capiot",       "name": "Amaury Capiot",        "pcs": "amaury-capiot",             "nat": "🇧🇪", "team": "Jayco AlUla"},
    {"id": "rodriguez",    "name": "Cristián Rodríguez",   "pcs": "cristian-rodriguez-martin", "nat": "🇪🇸", "team": "XDS Astana"},
    {"id": "garciaPierna", "name": "Raúl García Pierna",   "pcs": "raul-garcia-pierna",        "nat": "🇪🇸", "team": "Movistar Team"},
    {"id": "guglielmi",    "name": "Simon Guglielmi",      "pcs": "simon-guglielmi",           "nat": "🇫🇷", "team": "St Michel-Auber93"},
    {"id": "huys",         "name": "Laurens Huys",         "pcs": "laurens-huys",              "nat": "🇧🇪", "team": "Nice Métropole Côte d'Azur"},
    {"id": "svestad",      "name": "E. Svestad-Bårdseng",  "pcs": "embret-svestad-bardseng",   "nat": "🇳🇴", "team": "INEOS Grenadiers"},
    {"id": "leBerre",      "name": "Mathis Le Berre",      "pcs": "mathis-le-berre",           "nat": "🇫🇷", "team": "TotalEnergies"},
    {"id": "grondin",      "name": "Donavan Grondin",      "pcs": "donavan-grondin",           "nat": "🇫🇷", "team": "Veloce Club Rouen 76"},
    {"id": "tjotta",       "name": "Martin Tjøtta",        "pcs": "martin-tjotta",             "nat": "🇳🇴", "team": "Uno-X Mobility"},
    {"id": "rouland",      "name": "Louis Rouland",        "pcs": "louis-rouland",             "nat": "🇫🇷", "team": "Cofidis"},
    {"id": "thierry",      "name": "Pierre Thierry",       "pcs": "pierre-thierry",            "nat": "🇫🇷", "team": "TotalEnergies"},
    {"id": "lozouet",      "name": "Léandre Lozouet",      "pcs": "leandre-lozouet",           "nat": "🇫🇷", "team": "CIC Pro Cycling Academy"},
]

# Barème PCS simplifié pour estimation
PCS_POINTS = {
    "1.UWT": {1:400,2:300,3:225,4:175,5:140,6:110,7:85,8:65,9:50,10:40},
    "2.UWT": {1:200,2:160,3:130,4:100,5:80,6:65,7:50,8:40,9:30,10:20},
    "1.Pro": {1:100,2:80,3:65,4:50,5:40,6:30,7:25,8:20,9:15,10:10},
    "2.Pro": {1:80,2:60,3:50,4:40,5:30,6:25,7:20,8:15,9:10,10:8},
    "1.1":   {1:50, 2:35,3:25,4:18,5:14,6:11,7:8, 8:6, 9:4, 10:3},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CyclismeTracker/1.0)",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError) as e:
            print(f"  ⚠ Erreur fetch ({i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(3)
    return None

def parse_pcs_results(html, rider_id, year="2026"):
    """Parse la page résultats PCS d'un coureur pour l'année donnée."""
    results = []
    if not html:
        return results

    # Cherche le bloc résultats de l'année
    year_pattern = re.compile(
        rf'<h3[^>]*>\s*{year}\s*</h3>(.*?)(?=<h3|$)',
        re.DOTALL | re.IGNORECASE
    )
    year_match = year_pattern.search(html)
    if not year_match:
        # Fallback : cherche directement les lignes de résultats avec 2026
        year_block = html
    else:
        year_block = year_match.group(1)

    # Pattern pour extraire les lignes résultats
    row_pattern = re.compile(
        r'<li[^>]*>\s*'
        r'(?:<span[^>]*>)?(\d{1,3}(?:st|nd|rd|th)?|DNF|DNS|OTL|ABD)?(?:</span>)?\s*'
        r'<a[^>]*href="([^"]+race[^"]+)"[^>]*>([^<]+)</a>\s*'
        r'(?:.*?<span[^>]*class="[^"]*race-cat[^"]*"[^>]*>([^<]+)</span>)?',
        re.DOTALL | re.IGNORECASE
    )

    # Approche alternative : parse les lignes de résultats de façon plus simple
    # Cherche des patterns comme "1st Race Name (cat)"
    simple_pattern = re.compile(
        r'(\d{1,3})\s*<a[^>]*href="(/race/[^"]+/2026[^"]*)"[^>]*>([^<]{3,80})</a>',
        re.IGNORECASE
    )

    for m in simple_pattern.finditer(year_block):
        pos_str, race_url, race_name = m.group(1), m.group(2), m.group(3).strip()
        try:
            pos = int(pos_str)
        except ValueError:
            continue

        # Ignore les classements secondaires (points, KOM, jeunes)
        if any(x in race_name.lower() for x in ['points', 'kom', 'youth', 'young', 'jeunes']):
            continue

        # Détermine la catégorie depuis l'URL
        cat = "1.1"
        if "tour-de-france" in race_url or "giro-d-italia" in race_url or "vuelta" in race_url:
            cat = "gc"
        elif any(x in race_url for x in ["paris-roubaix","tour-de-flandres","liege","milan-san","strade","amstel","lombardia"]):
            cat = "wt"

        # Cherche la catégorie officielle dans le HTML autour du match
        cat_search = re.search(r'\((\d\.\w+)\)', race_name)
        if cat_search:
            cat_raw = cat_search.group(1)
            race_name = race_name.replace(f"({cat_raw})", "").strip()
            if "UWT" in cat_raw:
                cat = "wt"
            elif "Pro" in cat_raw:
                cat = "pro"
            else:
                cat = cat_raw

        # Estime les points PCS
        pts_map = PCS_POINTS.get("1.UWT" if cat == "wt" else
                                  "2.UWT" if cat == "gc" else
                                  "1.Pro" if cat == "pro" else "1.1", {})
        pts = pts_map.get(pos, 0)

        # Extrait la date depuis l'URL si possible
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', race_url)
        if date_match:
            date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        else:
            date_str = year

        results.append({
            "rider": rider_id,
            "race": race_name,
            "date": date_str,
            "cat": cat,
            "pos": pos,
            "pts": pts,
            "note": "",
            "source": "pcs"
        })

    return results

def scrape_rider(rider):
    """Scrape les résultats 2026 d'un coureur depuis PCS."""
    url = f"https://www.procyclingstats.com/rider/{rider['pcs']}/results/all"
    print(f"  Scraping {rider['name']}...")
    html = fetch(url)
    results = parse_pcs_results(html, rider["id"])
    print(f"    → {len(results)} résultat(s) trouvé(s)")
    time.sleep(2)  # Respecte le serveur PCS
    return results

def load_existing():
    """Charge les données existantes (résultats manuels + précédents scrapes)."""
    path = "data/results.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"results": [], "last_update": None, "manual": []}

def merge_results(existing, scraped):
    """
    Fusionne résultats scrapés + résultats manuels.
    Les résultats manuels (source='manual') ne sont jamais écrasés.
    """
    manual = [r for r in existing.get("results", []) if r.get("source") == "manual"]
    
    # Déduplique les résultats scrapés
    seen = set()
    deduped = []
    for r in scraped:
        key = f"{r['rider']}|{r['race']}|{r['date']}"
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    # Ajoute les manuels qui ne sont pas déjà dans les scrapés
    for m in manual:
        key = f"{m['rider']}|{m['race']}|{m['date']}"
        if key not in seen:
            deduped.append(m)

    # Trie par date décroissante
    deduped.sort(key=lambda r: r.get("date",""), reverse=True)
    return deduped

def main():
    print("🚴 Démarrage du scraper Ex-Arkéa Tracker 2026")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    os.makedirs("data", exist_ok=True)
    existing = load_existing()

    all_scraped = []
    for rider in RIDERS:
        results = scrape_rider(rider)
        all_scraped.extend(results)

    merged = merge_results(existing, all_scraped)

    output = {
        "last_update": datetime.now().isoformat(),
        "riders": RIDERS,
        "results": merged
    }

    with open("data/results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(merged)} résultats sauvegardés dans data/results.json")
    print(f"   Dont {len([r for r in merged if r.get('source')=='manual'])} résultats manuels conservés")

if __name__ == "__main__":
    main()
