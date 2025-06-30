import requests
import pandas as pd
from io import StringIO
import os

# === Authentification ===
USERNAME = "yasminedri"
PASSWORD = "@X6j7cbuy"
auth_url = "https://admindata.atmo-france.org/api/login"

auth_response = requests.post(auth_url, json={"username": USERNAME, "password": PASSWORD})
if auth_response.status_code != 200:
    raise Exception("❌ Échec de l'authentification")

token = auth_response.json()['token']
headers = {"Authorization": f"Bearer {token}"}

# === Création du dossier data s'il n'existe pas ===
os.makedirs("data", exist_ok=True)

# === Indices ATMO ===
url_atmo = "https://admindata.atmo-france.org/api/v2/data/indices/atmo"
params_atmo = {
    "format": "csv",
    "code_zone": "13055,13001,83137,06088,84007,13004,05061,04070",
    "date_historique": "2024-06-01",
    "date": "2025-06-01"
}
response = requests.get(url_atmo, headers=headers, params=params_atmo)
df_atmo = pd.read_csv(StringIO(response.text))
df_atmo.to_csv("data/indices_atmo.csv", index=False)
print("indices_atmo.csv enregistré")

# === Inventaire des émissions ===
url_emissions = "https://admindata.atmo-france.org/api/v2/data/inventaires/emissions"
params_emissions = {
    "format": "csv",
    "secteur": "5,6,7,34,219"
}
response = requests.get(url_emissions, headers=headers, params=params_emissions)
df_emissions = pd.read_csv(StringIO(response.text))
df_emissions.to_csv("data/emissions_par_secteur.csv", index=False)
print(" emissions_par_secteur.csv enregistré")

# === Épisodes de pollution - 3 jours (région Sud uniquement)
url_episodes = "https://admindata.atmo-france.org/api/v2/data/episodes/3jours"

params_episodes = {
    "format": "csv",
    "code_zone": "04,05,06,13,83,84"
}

response = requests.get(url_episodes, headers=headers, params=params_episodes)
df_episodes = pd.read_csv(StringIO(response.text))
df_episodes.to_csv("data/episodes_3jours.csv", index=False)
print(" episodes_3jours.csv enregistré ")


# === Indices pollens ===
url_pollens = "https://admindata.atmo-france.org/api/v2/data/indices/pollens"
params_pollens = {
    "format": "csv",
    "code_zone": "13055,13001,83137,06088,84007,13004,05061,04070"
}
response = requests.get(url_pollens, headers=headers, params=params_pollens)
df_pollens = pd.read_csv(StringIO(response.text))
df_pollens.to_csv("data/indices_pollens.csv", index=False)
print(" indices_pollens.csv enregistré")
