import os, re, requests, pandas as pd
from bs4 import BeautifulSoup


BASE = "https://files.data.gouv.fr/lcsqa/concentrations-de-polluants-atmospheriques-reglementes/temps-reel/2025/"
os.makedirs("data/raw", exist_ok=True)

html = requests.get(BASE, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

rows = []
for a in soup.find_all("a"):
    name = a.get_text(strip=True)
    if name.endswith(".csv") and name.startswith("FR_E2_"):
        # La ligne complète (nom + espaces + date + taille) est dans le parent (listing de répertoire)
        line = a.parent.get_text(" ", strip=True)
        # On essaie de récupérer date maj et taille (optionnel si le format change)
        m = re.search(r"(FR_E2_[\d\-]+\.csv)\s+(\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2})\s+(\d+)", line)
        rows.append({
            "filename": name,
            "url": BASE + name,
            "last_modified": m.group(2) if m else None,
            "size_bytes": int(m.group(3)) if m else None
        })

df = pd.DataFrame(rows).sort_values("filename").reset_index(drop=True)
print(df.head(5))
df.to_csv("data/raw/webscraping_lcsqa_index_2025.csv", index=False)
print("OK -> data/raw/webscraping_lcsqa_index_2025.csv")



# Charger le CSV obtenu avec le scraping
df = pd.read_csv("/Users/yasmine/Documents/projet-data-QA-1/data/raw/webscraping_lcsqa_index_2025.csv")

# On crée un dossier pour stocker les fichiers téléchargés
outdir = "/Users/yasmine/Documents/projet-data-QA-1/data/raw/crawling_lcsqa"
os.makedirs(outdir, exist_ok=True)

# On limite à 3 fichiers pour la démonstration
for _, row in df.head(3).iterrows():
    url = row["url"]
    filename = os.path.join(outdir, row["filename"])
    
    r = requests.get(url, timeout=60)
    r.raise_for_status()  # Stoppe si erreur HTTP
    with open(filename, "wb") as f:
        f.write(r.content)
    
    print(f"Téléchargé : {row['filename']} ({len(r.content)} octets)")

print(f"✅ Web crawling terminé — fichiers enregistrés dans {outdir}")

