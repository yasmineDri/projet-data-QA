import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# === Paramètres généraux ===
villes = {
    "Marseille": 80,
    "Nice": 75,
    "Toulon": 60,
    "Avignon": 50,
    "Aix-en-Provence": 55,
    "Arles": 40,
    "Gap": 30,
    "Digne-les-Bains": 25
}

# Période cible : aujourd'hui → 31 décembre
start_date = datetime.now().date()
end_date = datetime(2025, 12, 31).date()

# Création des dates et heures (6h à 22h, toutes les heures)
dates = pd.date_range(start=start_date, end=end_date, freq='D')
heures = list(range(6, 23))

# Génération des données
rows = []

for date in dates:
    mois = date.month
    jour_semaine = date.weekday()  # 0 = lundi, 6 = dimanche
    for heure in heures:
        for ville, base_trafic in villes.items():
            # Base selon ville
            trafic = base_trafic

            # Modulation selon heure (pointe matin/soir)
            if 7 <= heure <= 9 or 17 <= heure <= 19:
                trafic *= 1.3
            elif 12 <= heure <= 14:
                trafic *= 0.8
            else:
                trafic *= 0.6

            # Modulation week-end
            if jour_semaine >= 5:
                trafic *= 0.7

            # Modulation août (vacances)
            if mois == 8:
                trafic *= 0.75
            # Modulation décembre (trafic modéré)
            elif mois == 12:
                trafic *= 0.9

            # Variabilité réaliste
            trafic += np.random.normal(0, 5)
            trafic = max(0, min(100, round(trafic, 1)))  # borné 0-100

            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "heure": f"{heure:02d}:00",
                "ville": ville,
                "trafic": trafic
            })

# Création DataFrame
df_trafic = pd.DataFrame(rows)

# Sauvegarde CSV
os.makedirs("data/synthetique", exist_ok=True)
df_trafic.to_csv("data/synthetique/trafic_routier_synthetique.csv", index=False, sep=";")
print(f"✅ Fichier généré : {len(df_trafic)} lignes dans trafic_routier_synthetique.csv")
