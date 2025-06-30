import pandas as pd

def clean_indices_atmo(df):
    """
    Nettoyage des données de la table indices_atmo :
    - Supprime la colonne 'gml_id2' si présente.
    - Convertit les colonnes de dates en format datetime : date_maj.
    """
    df = df.drop(columns=["gml_id2"], errors='ignore')
    df["date_maj"] = pd.to_datetime(df["date_maj"], errors='coerce')
    return df

def clean_mesures_polluants(df):
    """
    Nettoyage des données de la table mesures_polluants :
    - Convertit la colonne 'date_debut' en datetime.
    - Remplace les virgules par des points dans la colonne 'valeur'.
    - Convertit 'valeur' en numérique (float).
    - Supprime les lignes avec valeur manquante dans 'valeur'.
    """
    df["date_debut"] = pd.to_datetime(df["date_debut"], errors='coerce')
    df["valeur"] = df["valeur"].astype(str).str.replace(",", ".")
    df["valeur"] = pd.to_numeric(df["valeur"], errors='coerce')
    df = df.dropna(subset=["valeur"])
    return df

def clean_emissions_par_secteur(df):
    """
    Nettoyage des données de la table emissions_par_secteur :
    - Convertit la colonne 'date_maj' en datetime.
    """
    df["date_maj"] = pd.to_datetime(df["date_maj"], errors='coerce')
    return df

def clean_indices_pollens(df):
    """
    Nettoyage des données de la table indices_pollens :
    - Supprime la colonne 'name' si elle existe (souvent vide).
    - Convertit les colonnes de dates en format datetime : date_maj.
    """
    df = df.drop(columns=["name"], errors='ignore')
    df["date_maj"] = pd.to_datetime(df["date_maj"], errors='coerce')
    return df

def clean_episodes_3jours(df):
    """
    Nettoyage des données de la table episodes_3jours :
    - Convertit les colonnes de dates en format datetime : date_maj, date_dif, date_ech.
    """
    df["date_maj"] = pd.to_datetime(df["date_maj"], errors='coerce')
    return df
