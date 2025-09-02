import pandas as pd

def clean_indices_atmo(df):
    import pandas as pd

    # Renames (ok si colonnes absentes)
    df = df.rename(columns={
        'aasqa': 'code_aasqa',
        'date_maj': 'date_mise_a_jour',
        'code_no2': 'indice_no2',
        'code_o3': 'indice_o3',
        'code_pm10': 'indice_pm10',
        'code_pm25': 'indice_pm25',
        'code_qual': 'indice_qualite_air',
        'code_so2': 'indice_so2',
        'code_zone': 'code_insee',
        'coul_qual': 'couleur_qualite',
        'date_dif': 'date_diffusion',
        'date_ech': 'date_echeance',
        'epsg_reg': 'epsg_regionale',
        'lib_qual': 'libelle_qualite',
        'lib_zone': 'nom_commune',
        'source': 'source_donnee',
        'x_reg': 'x_regional',
        'x_wgs84': 'lon',
        'y_reg': 'y_regional',
        'y_wgs84': 'lat'
    })

    # 1) Eviter le KeyError: convertir dates seulement si la colonne existe
    for col in ["date_mise_a_jour", "date_diffusion", "date_echeance"]:
        if col in df.columns:
            # 2) Virer l'avertissement fuseaux : utc=True puis retirer le tz
            s = pd.to_datetime(df[col], errors='coerce', utc=True)
            df[col] = s.dt.tz_localize(None)

    # code_insee en string 5 chiffres si présent
    if 'code_insee' in df.columns:
        df['code_insee'] = df['code_insee'].astype(str).str.zfill(5)

    # 3) Sélectionner seulement les colonnes existantes (sinon KeyError)
    cols_final = [
        'code_insee', 'date_echeance', 'indice_no2', 'indice_o3', 'indice_pm10',
        'indice_pm25', 'indice_qualite_air', 'couleur_qualite',
        'date_diffusion', 'date_mise_a_jour', 'libelle_qualite', 'type_zone',
        'lon', 'lat'
    ]
    df = df[[c for c in cols_final if c in df.columns]]

    # Doublons
    df = df.drop_duplicates()

    # Si la date d’échéance manque mais on a la diffusion, utiliser diffusion comme fallback
    if 'date_echeance' in df.columns and df['date_echeance'].isna().all() and 'date_diffusion' in df.columns:
        df['date_echeance'] = df['date_diffusion'].dt.date

    # Ne garder que les lignes avec code_insee si la colonne existe
    if 'code_insee' in df.columns:
        df = df.dropna(subset=['code_insee'])

    return df


def clean_emissions_par_secteur(df):
    import pandas as pd

    # Renommer 'name' → 'region'
    df = df.rename(columns={'name': 'region'})

    df['date_maj'] = pd.to_datetime(df['date_maj'], errors='coerce')

    # Convertir types
    df['region'] = df['region'].astype(str)
    df['code_pcaet'] = df['code_pcaet'].astype(str)
    df['code'] = df['code'].astype(str)

    # Colonnes finales à garder (exactement comme SQL)
    cols_final = [
        'region', 'date_maj', 'superficie', 'population',
        'pm25', 'pm10', 'nox', 'ges',
        'code_pcaet', 'code'
    ]
    df = df[cols_final]

    # Supprimer doublons
    df = df.drop_duplicates()

    # Supprimer lignes incomplètes
    df = df.dropna(subset=['region', 'date_maj'])

    return df





def clean_indices_pollens(df):
    # Conversion des dates
    df['date_ech'] = pd.to_datetime(df['date_ech'], errors='coerce')
    df['date_maj'] = pd.to_datetime(df['date_maj'], errors='coerce')

    # Créer code_insee à partir de code_zone
    df['code_insee'] = df['code_zone'].astype(str).str.zfill(5)

    # Renommer 'date_ech' → 'date_echeance' AVANT d’utiliser dans cols_final
    df = df.rename(columns={'date_ech': 'date_echeance'})

    # Colonnes finales à garder (alignées avec SQL)
    cols_final = [
        'code_insee', 'date_echeance', 'alerte',
        'code_ambr', 'code_arm', 'code_aul', 'code_boul',
        'code_gram', 'code_oliv',
        'conc_ambr', 'conc_arm', 'conc_aul', 'conc_boul',
        'conc_gram', 'conc_oliv',
        'pollen_resp', 'source'
    ]

    # Garder les colonnes utiles
    df = df[cols_final]

    # Supprimer doublons
    df = df.drop_duplicates()

    # Supprimer lignes incomplètes
    df = df.dropna(subset=['code_insee', 'date_echeance'])

    return df


def clean_episodes_3jours(df):
    # Renommer date_ech → date_echeance (aligné SQL)
    df = df.rename(columns={'date_ech': 'date_echeance'})

    # Conversion des dates
    df['date_echeance'] = pd.to_datetime(df['date_echeance'], errors='coerce').dt.date
    df['date_maj'] = pd.to_datetime(df['date_maj'], errors='coerce')
    df['date_dif'] = pd.to_datetime(df['date_dif'], errors='coerce')

    # Garder colonnes utiles
    cols_final = ['code_zone', 'code_pol', 'lib_pol', 'date_echeance', 'etat']
    df = df[cols_final]

    # Supprimer doublons
    df = df.drop_duplicates()

    # Supprimer lignes incomplètes
    df = df.dropna(subset=['code_zone', 'code_pol', 'date_echeance'])

    return df


def clean_mesures(df):
    df = df.rename(columns={
        "id_site": "id_station",
        "num_stat_euro": "code_station",
        "nom_site": "nom_station",
        "adrs": "adresse",
        "nom_compose": "polluant",
        "dh": "datetime",
        "compose_iso": "code_polluant",
        "lon": "longitude",
        "lat": "latitude",
        "concentration": "valeur",
        "code": "code_indice",
        "couleur_hexa": "couleur_indice",
        "qualificatif": "qualificatif"
    })

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df["date"] = df["datetime"].dt.date
        df["heure"] = df["datetime"].dt.time

    # Supprimer les doublons sur la clé primaire (id_station, datetime, polluant)
    df = df.drop_duplicates(subset=["id_station", "datetime", "polluant"])

    return df

def clean_meteo(df):
    import pandas as pd

    # Conversion colonne 'time' en datetime
    df['time'] = pd.to_datetime(df['time'], errors='coerce')

    # Nettoyage : suppression lignes sans ville ou time
    df = df.dropna(subset=['ville', 'time'])

    # Conversion types pour cohérence
    df['ville'] = df['ville'].astype(str)
    df['temperature_2m'] = df['temperature_2m'].astype(float)
    df['relative_humidity_2m'] = df['relative_humidity_2m'].astype(int)
    df['precipitation'] = df['precipitation'].astype(float)
    df['windspeed_10m'] = df['windspeed_10m'].astype(float)

    # Supprimer doublons éventuels
    df = df.drop_duplicates()

    return df

# --- à AJOUTER tout en bas de clean.py ---
def run_all_cleans():
    """
    Ici tu ne lis/écris rien directement si ton clean est déjà dans transformer_all.
    Si tu fais déjà le nettoyage dans transformer_all.py (c'est le cas),
    on ne fait rien ici et on laisse transformer_all.run_all_transforms() produire
    les *clean.csv*. On garde cette fonction pour Airflow.
    """
    return {"status": "noop_clean"}