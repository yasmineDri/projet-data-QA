import os
import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
import chardet  # pour encodage

# === OUTILS GÉNÉRIQUES ===
def save_csv(df, path):
    df.to_csv(path, index=False, sep=";", encoding="utf-8")
    print(f"[{datetime.now()}] ✅ {os.path.basename(path)} sauvegardé")

# === AUTHENTIFICATION ATMO FRANCE ===
def authentifier():
    USERNAME = "yasminedri"
    PASSWORD = "@X6j7cbuy"
    auth_url = "https://admindata.atmo-france.org/api/login"
    response = requests.post(auth_url, json={"username": USERNAME, "password": PASSWORD})
    if response.status_code != 200:
        raise Exception("❌ Échec de l'authentification")
    return {"Authorization": f"Bearer {response.json()['token']}"}

# === INDICES ATMO  ===
def collect_indices_atmo(headers):
    url = "https://admindata.atmo-france.org/api/v2/data/indices/atmo"
    code_zone = "13055,13001,83137,06088,84007,13004,05061,04070"

    today = datetime.today().date()
    start_date = today - timedelta(days=30)  # on veut les 30 derniers jours
    delta = timedelta(days=7)  # appel par tranche de 7 jours

    all_dfs = []

    while start_date < today:
        end_date = min(start_date + delta, today)

        params = {
            "format": "csv",
            "code_zone": code_zone,
            "date_historique": start_date.isoformat(),
            "date": end_date.isoformat()
        }

        print(f"🔄 Requête de {start_date} à {end_date}...")

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            all_dfs.append(df)
        except Exception as e:
            print(f"❌ Erreur sur la période {start_date} à {end_date} : {e}")

        start_date = end_date + timedelta(days=1)

    if all_dfs:
        df_final = pd.concat(all_dfs, ignore_index=True)
        save_csv(df_final, "/data/raw/atmo/indices_atmo.csv")
        print("✅ Données indices ATMO sauvegardées.")
    else:
        print("⚠️ Aucune donnée ATMO collectée.")



# === EMISSIONS PAR SECTEUR ===
def collect_emissions(headers):
    url = "https://admindata.atmo-france.org/api/v2/data/inventaires/emissions"
    params = {"format": "csv", "secteur": "5,6,7,34,219"}
    response = requests.get(url, headers=headers, params=params)
    df = pd.read_csv(StringIO(response.text))
    save_csv(df, "/data/raw/atmo/emissions_par_secteur.csv")

# === EPISODES DE POLLUTION ===
def collect_episodes(headers):
    url = "https://admindata.atmo-france.org/api/v2/data/episodes/3jours"
    params = {"format": "csv", "code_zone": "04,05,06,13,83,84"}
    response = requests.get(url, headers=headers, params=params)
    df = pd.read_csv(StringIO(response.text))
    save_csv(df, "/data/raw/atmo/episodes_3jours.csv")

# === INDICES POLLENS ===
def collect_pollens(headers):
    url = "https://admindata.atmo-france.org/api/v2/data/indices/pollens"
    params = {"format": "csv", "code_zone": "13055,13001,83137,06088,84007,13004,05061,04070"}
    response = requests.get(url, headers=headers, params=params)
    df = pd.read_csv(StringIO(response.text))
    save_csv(df, "/data/raw/atmo/indices_pollens.csv")

# === MÉTÉO HISTORIQUE (Open-Meteo) ===
def collect_meteo_open_meteo():
    villes_coords = {
        "Marseille": (43.2965, 5.3698),
        "Nice": (43.7102, 7.2620),
        "Toulon": (43.1242, 5.9280),
        "Avignon": (43.9493, 4.8055),
        "Aix-en-Provence": (43.5297, 5.4474),
        "Arles": (43.6766, 4.6278),
        "Gap": (44.5590, 6.0795),
        "Digne-les-Bains": (44.0921, 6.2310)
    }

    today = datetime.today().date()
    one_month_ago = today - timedelta(days=30)
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = "hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m"

    os.makedirs("/data/raw/meteo", exist_ok=True)
    all_dfs = []

    for ville, (lat, lon) in villes_coords.items():
        print(f"🔄 Météo pour {ville}")
        url = (
            f"{base_url}?latitude={lat}&longitude={lon}&{params}"
            f"&start_date={one_month_ago.isoformat()}&end_date={today.isoformat()}"
            f"&timezone=Europe%2FParis"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()["hourly"]
            df = pd.DataFrame(data)
            df["ville"] = ville
            all_dfs.append(df)
        except Exception as e:
            print(f"❌ Erreur météo pour {ville} : {e}")

    if all_dfs:
        df_all = pd.concat(all_dfs, ignore_index=True)
        df_all.to_csv("/data/raw/meteo/meteo.csv", index=False, sep=";")
        print("✅ Données météo enregistrées dans meteo.csv")
    else:
        print("❌ Aucune donnée météo collectée.")

# === MESURES HORAIRES ATMOSUD ===
def collect_mesures_horaires_atmosud():
    print("🔄 Collecte des mesures horaires AtmoSud...")

    base_url = "https://api.atmosud.org/iqa2021/station/mesures/indices/horaire"
    params = {
        "format_indice": "valeur,qualificatif",
        "indice": "all",
        "format": "csv"
    }

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()

        detected = chardet.detect(response.content)
        contenu = response.content.decode(detected['encoding'], errors="replace")
        df = pd.read_csv(StringIO(contenu), sep=",", encoding_errors="replace")

        os.makedirs("/data/raw/atmo", exist_ok=True)
        save_csv(df, "/data/raw/atmo/mesures_horaires_atmosud2.csv")
        print("✅ Sauvegarde réussie.")
    except Exception as e:
        print(f"❌ Erreur mesures horaires AtmoSud : {e}")

# === POUR AIRFLOW ===
def run_collecte():
    print("✅ Script de collecte lancé")
    os.makedirs("/data/raw/atmo", exist_ok=True)
    headers = authentifier()
    collect_indices_atmo(headers)
    collect_emissions(headers)
    collect_episodes(headers)
    collect_pollens(headers)
    collect_meteo_open_meteo()
    collect_mesures_horaires_atmosud()
