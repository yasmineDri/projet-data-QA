import os
import datetime as dt
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
import folium.plugins
import streamlit.components.v1 as components
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# -----------------------------
# CONFIG & CONNEXION
# -----------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "qualair_db")
DB_USER = os.getenv("DB_USER", "yasminedri")
DB_PASS = os.getenv("DB_PASS", "qualair")

@st.cache_resource
def get_db_engine():
    """Crée et retourne le moteur de base de données."""
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        return engine
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        return None

engine = get_db_engine()
if engine is None:
    st.stop()
    
# -----------------------------
# DÉFINITION DE LA MISE EN PAGE
# -----------------------------
st.set_page_config(
    page_title="Dashboard – Qualité de l'air Région Sud",
    page_icon="🌬️",
    layout="wide",
)


# -----------------------------
# PALETTE & MAPPINGS
# -----------------------------
PRIMARY = "#3B5998"        # Bleu doux
ACCENT = "#A7C7E7"         # Bleu clair pastel
SUCCESS = "#90EE90"        # Vert pastel
WARN = "#FFD580"           # Orange pastel
ALERT = "#FF9999"          # Rouge pastel
PALETTE_MULTI = px.colors.qualitative.Plotly
PALETTE_PASTEL = px.colors.qualitative.Pastel1
BACKGROUND_COLOR = "#F7FAFC"   # fond général
CARD_BACKGROUND = "#F0F4F8"    # cartes pastel

VILLES = {
    "Marseille": {"lat": 43.2965, "lon": 5.3698, "insee": "13055", "dept_code": "13"},
    "Aix-en-Provence": {"lat": 43.5297, "lon": 5.4474, "insee": "13001", "dept_code": "13"},
    "Toulon": {"lat": 43.1242, "lon": 5.9280, "insee": "83137", "dept_code": "83"},
    "Nice": {"lat": 43.7102, "lon": 7.2620, "insee": "06088", "dept_code": "06"},
    "Avignon": {"lat": 43.9493, "lon": 4.8055, "insee": "84007", "dept_code": "84"},
    "Arles": {"lat": 43.6766, "lon": 4.6278, "insee": "13004", "dept_code": "13"},
    "Gap": {"lat": 44.5590, "lon": 6.0795, "insee": "05061", "dept_code": "05"},
    "Digne-les-Bains": {"lat": 44.0921, "lon": 6.2310, "insee": "04070", "dept_code": "04"},
}

DEPARTEMENTS = {
    '04': "Alpes-de-Haute-Provence",
    '05': "Hautes-Alpes",
    '06': "Alpes-Maritimes",
    '13': "Bouches-du-Rhône",
    '83': "Var",
    '84': "Vaucluse",
}

PCAET_SECTEURS = {
    '5': "Agriculture",
    '6': "Transport routier",
    '7': "Autres transports",
    '34': "Résidentiel - Tertiaire",
    '219': "Industrie & Énergie",
}

POLLEN_NIVEAUX = {
    1: {"libelle": "Faible", "couleur": SUCCESS},
    2: {"libelle": "Modéré", "couleur": "#FFD580"},
    3: {"libelle": "Élevé", "couleur": WARN},
    4: {"libelle": "Très Élevé", "couleur": ALERT},
}

RECOMMANDATIONS_POLLEN = {
    1: "🌱 Faible risque. Vous pouvez profiter des activités extérieures sans précaution particulière.",
    2: "⚠️ Risque modéré. Limitez les activités en extérieur en cas de symptômes.",
    3: "🚨 Risque élevé. Évitez les sorties prolongées et gardez vos fenêtres fermées, particulièrement le matin.",
    4: "🔴 Très fort risque. Il est recommandé de rester à l'intérieur et de prendre un traitement adapté après avis médical.",
}

COULEURS_ATMO = {
    "Bon": "#B2FBA5",
    "Moyen": "#FFF44F",
    "Dégradé": "#F9AB59",
    "Mauvais": "#FF6961",
    "Très mauvais": "#C3B1E1",
    "Extrêmement mauvais": "black"
}

RECOMMANDATIONS_ATMO = {
    "Bon": "💚 Qualité de l'air bonne. Profitez pleinement de vos activités extérieures habituelles.",
    "Moyen": "👍 Qualité de l'air acceptable. La pratique d'activités physiques et sportives en plein air n'est pas limitée.",
    "Dégradé": "⚠️ Qualité de l'air dégradée. Les personnes sensibles (asthmatiques, allergiques, etc.) devraient limiter leurs activités physiques intenses en extérieur.",
    "Mauvais": "🔴 Qualité de l'air mauvaise. Évitez les activités sportives et limitez les déplacements en plein air. Les personnes vulnérables devraient rester à l'intérieur.",
    "Très mauvais": "⛔️ Qualité de l'air très mauvaise. Reportez toutes vos activités sportives. Restez chez vous et évitez toute exposition prolongée à la pollution.",
    "Extrêmement mauvais": "💀 Urgence sanitaire. Il est impératif de rester à l'intérieur et de réduire au minimum les efforts physiques. Surveillez les symptômes.",
}

POLLUANTS = ['PM10', 'NO2', 'O3']
POLLUANTS_EMISSIONS = {'PM25': 'pm25', 'PM10': 'pm10', 'NOx': 'nox'}
SEUILS = {"NO2": 40, "PM10": 50, "O3": 120}

# -----------------------------
# HELPERS SQL
# -----------------------------
@st.cache_data(ttl=300)
def df_sql(q, params=None):
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as con:
            return pd.read_sql(text(q), con, params=params or {})
    except Exception as e:
        st.error(f"Erreur lors de l'exécution de la requête SQL : {e}")
        return pd.DataFrame()

def get_mesures_courantes_by_ville_polluant(ville, polluant):
    q = """
    SELECT
        s.nom_station,
        s.latitude,
        s.longitude,
        mj.polluant,
        mj.valeur,
        mj.qualificatif
    FROM prod.mesure_journaliere mj
    JOIN prod.station s ON mj.id_station = s.id_station
    WHERE s.ville = :ville AND mj.polluant = :polluant AND mj.datetime >= NOW() - INTERVAL '1 day'
    ORDER BY mj.datetime DESC;
    """
    return df_sql(q, {"ville": ville, "polluant": polluant})

def get_indice_atmo_by_date(insee, date_select):
    q = """
    SELECT date_echeance, indice_qualite_air, libelle_qualite, couleur_qualite
    FROM prod.indice_atmo
    WHERE code_insee = :insee AND date_echeance::date = :date_select
    ORDER BY date_echeance DESC
    LIMIT 1
    """
    return df_sql(q, {"insee": insee, "date_select": date_select})

def get_polluant_dominant_du_jour(insee):
    q = """
    SELECT polluant, AVG(valeur) AS moyenne
    FROM prod.mesure_journaliere mj
    JOIN prod.station s ON mj.id_station = s.id_station
    WHERE s.code_insee = :insee
      AND mj.datetime >= NOW() - INTERVAL '24 hours'
      AND polluant IN ('PM10', 'NO2', 'O3')
    GROUP BY polluant
    ORDER BY moyenne DESC
    LIMIT 1
    """
    df = df_sql(q, {"insee": insee})
    if df.empty:
        return None, None
    return df.iloc[0]["polluant"], round(float(df.iloc[0]["moyenne"]), 1)

def get_mesures_actuelles_tous_polluants(ville, polluants):
    """Récupère les concentrations les plus récentes pour une liste de polluants dans une ville donnée."""
    q = f"""
    SELECT
        mj.polluant,
        AVG(mj.valeur) AS valeur_moyenne
    FROM prod.mesure_journaliere mj
    JOIN prod.station s ON mj.id_station = s.id_station
    WHERE s.ville = :ville
      AND mj.polluant IN ({', '.join([f"'{p}'" for p in polluants])})
      AND mj.datetime >= NOW() - INTERVAL '24 hours'
    GROUP BY mj.polluant
    ORDER BY mj.polluant;
    """
    return df_sql(q, {"ville": ville})

def get_prevision_pollen_ville(insee):
    q = """
    SELECT
        date_echeance,
        pollen_resp,
        GREATEST(code_ambr, code_arm, code_aul, code_boul, code_gram, code_oliv) AS niveau_risque
    FROM prod.indice_pollen
    WHERE code_insee = :insee AND date_echeance >= CURRENT_DATE
    ORDER BY date_echeance ASC
    LIMIT 3
    """
    try:
        df = df_sql(q, {"insee": insee})
        if df.empty:
            st.warning("La table `indice_pollen` est vide pour la ville sélectionnée.")
        return df
    except Exception as e:
        st.error(f"Erreur lors de la récupération des prévisions de pollen : {e}")
        return pd.DataFrame()

def get_emissions_par_secteur_paca():
    q = """
    SELECT code_pcaet, SUM(ges) AS total_ges
    FROM prod.emission_par_secteur
    WHERE code = '93'
    GROUP BY code_pcaet
    ORDER BY total_ges DESC
    """
    df = df_sql(q)
    df['secteur'] = df['code_pcaet'].map(PCAET_SECTEURS)
    df['secteur'] = df['secteur'].fillna('Autre')
    return df

def get_emissions_by_sector_pollutant():
    q = """
    SELECT code_pcaet, pm25, pm10, nox
    FROM prod.emission_par_secteur
    WHERE code = '93'
    """
    df = df_sql(q)

    if not df.empty and 'code_pcaet' in df.columns:
        df_melted = df.melt(id_vars='code_pcaet',
                            value_vars=['pm25', 'pm10', 'nox'],
                            var_name='polluant',
                            value_name='quantite')
        
        df_melted['secteur'] = df_melted['code_pcaet'].map(PCAET_SECTEURS)
        df_melted['secteur'] = df_melted['secteur'].fillna('Autre')
        df_melted['polluant'] = df_melted['polluant'].map({'pm25': 'PM25', 'pm10': 'PM10', 'nox': 'NOx'})

        return df_melted
    else:
        st.error("Erreur: Colonnes 'code_pcaet' ou polluants manquantes dans la table d'émissions.")
        return pd.DataFrame()

def get_meteo_by_hour(ville, date_select, time_select):
    q = """
    SELECT time, temperature_2m, relative_humidity_2m, windspeed_10m
    FROM prod.meteo
    WHERE ville = :ville AND DATE(time) = :date_select AND EXTRACT(HOUR FROM time) = :time_select
    ORDER BY time DESC
    LIMIT 1
    """
    full_datetime = dt.datetime.combine(date_select, dt.time(time_select))
    return df_sql(q, {"ville": ville, "date_select": date_select, "time_select": time_select})

@st.cache_data(ttl=300)
def get_series_pollution_multi_polluants(ville_select, periode_debut, periode_fin):
    q = f"""
    SELECT DATE(mj.datetime) AS jour,
           mj.polluant,
           AVG(mj.valeur) AS valeur_moyenne
    FROM mesure_journaliere mj
    JOIN station s ON mj.id_station = s.id_station
    WHERE s.ville = '{ville_select}'
      AND mj.datetime BETWEEN '{periode_debut}' AND '{periode_fin}'
      AND mj.valeur IS NOT NULL
    GROUP BY jour, mj.polluant
    ORDER BY jour
    """
    return df_sql(q)

@st.cache_data(ttl=300)
def get_series_pollution_par_heure(ville_select, polluant_select, periode_debut, periode_fin):
    q = f"""
    SELECT DATE_TRUNC('hour', mj.datetime) AS heure,
           s.ville,
           mj.polluant,
           AVG(mj.valeur) AS valeur_moyenne
    FROM mesure_journaliere mj
    JOIN prod.station s ON mj.id_station = s.id_station
    WHERE s.ville = '{ville_select}'
      AND mj.polluant = '{polluant_select}'
      AND mj.datetime BETWEEN '{periode_debut}' AND '{periode_fin}'::date + interval '1 day'
      AND mj.valeur IS NOT NULL
    GROUP BY DATE_TRUNC('hour', mj.datetime), s.ville, mj.polluant
    ORDER BY heure
    """
    return df_sql(q)

@st.cache_data(ttl=300)
def get_all_correlation_data(ville_cible, periode_debut, periode_fin):
    try:
        # Charger polluants
        query_polluants = f"""
        SELECT m.datetime, m.polluant, m.valeur
        FROM mesure_journaliere m
        JOIN station s ON m.id_station = s.id_station
        WHERE s.ville = '{ville_cible}'
          AND m.datetime BETWEEN '{periode_debut}' AND '{periode_fin}'::date + interval '1 day'
        """
        df_polluants = pd.read_sql(query_polluants, engine)
        df_polluants["heure"] = pd.to_datetime(df_polluants["datetime"]).dt.floor("h").dt.tz_localize(None)
        df_polluants_pivot = (
            df_polluants.groupby(["heure", "polluant"])["valeur"].mean()
            .unstack()
            .reset_index()
        )

        # Charger trafic
        query_trafic = f"""
        SELECT date, heure, trafic
        FROM trafic_synthetique
        WHERE ville = '{ville_cible}'
          AND date BETWEEN '{periode_debut}' AND '{periode_fin}'
        """
        df_trafic = pd.read_sql(query_trafic, engine)
        df_trafic["heure"] = pd.to_datetime(df_trafic["date"].astype(str) + " " + df_trafic["heure"].astype(str))
        df_trafic["heure"] = df_trafic["heure"].dt.floor("h").dt.tz_localize(None)

        # Charger météo
        query_meteo = f"""
        SELECT time, temperature_2m, relative_humidity_2m, precipitation, windspeed_10m
        FROM meteo
        WHERE ville = '{ville_cible}'
          AND time BETWEEN '{periode_debut}' AND '{periode_fin}'::date + interval '1 day'
        """
        df_meteo = pd.read_sql(query_meteo, engine)
        df_meteo["heure"] = pd.to_datetime(df_meteo["time"]).dt.floor("h").dt.tz_localize(None)

        # Fusion des datasets
        df_all = df_polluants_pivot.merge(df_trafic[["heure", "trafic"]], on="heure", how="inner")
        df_all = df_all.merge(df_meteo[["heure", "temperature_2m", "relative_humidity_2m", "precipitation", "windspeed_10m"]],
                              on="heure", how="inner")
        
        # S'assurer que les colonnes sont bien numériques
        for col in df_all.columns:
            if col not in ['heure']:
                df_all[col] = pd.to_numeric(df_all[col], errors='coerce')

        return df_all

    except Exception as e:
        st.error(f"Erreur lors de la récupération des données de corrélation : {e}")
        return pd.DataFrame()

# -----------------------------
# NOUVELLE FONCTION POUR LA COMPARAISON INTER-VILLES
# -----------------------------
@st.cache_data(ttl=300)
def get_comparaison_inter_villes(polluant='NO2'):
    """Récupère la concentration moyenne d'un polluant par ville sur les 7 derniers jours."""
    query = f"""
    SELECT
        s.ville,
        AVG(mj.valeur) AS valeur_moyenne
    FROM
        mesure_journaliere mj
    JOIN
        station s ON mj.id_station = s.id_station
    WHERE
        mj.polluant = '{polluant}'
        AND mj.datetime >= NOW() - INTERVAL '7 days'
    GROUP BY
        s.ville
    ORDER BY
        valeur_moyenne DESC;
    """
    return df_sql(query)


# -----------------------------
# Fonctions de carte Folium
# -----------------------------
def generate_folium_map(df_mesures, ville_choisie):
    location = [VILLES[ville_choisie]["lat"], VILLES[ville_choisie]["lon"]]
    zoom_start = 12 if ville_choisie == "Marseille" else 10
    m = folium.Map(location=location, zoom_start=zoom_start, tiles="CartoDB positron")

    if not df_mesures.empty:
        heat_data = [[row['latitude'], row['longitude']] for index, row in df_mesures.iterrows()]
        folium.plugins.HeatMap(heat_data).add_to(m)

        for _, row in df_mesures.iterrows():
            couleur = COULEURS_ATMO.get(row["qualificatif"], "gray")
            taille = max(6, min(row["valeur"] / 2, 20))
            popup_text = f"<b>Station :</b> {row['nom_station']}<br><b>Polluant :</b> {row['polluant']}<br><b>Valeur :</b> {row['valeur']} µg/m³<br><b>Qualité :</b> {row['qualificatif']}"
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=taille,
                color=couleur,
                fill=True,
                fill_color=couleur,
                fill_opacity=0.85,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)

    legend_html = """
    <div style="position: fixed; top: 180px; left: 50px; width: 180px; background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px; border-radius:5px;">
    <b>Qualité de l'air</b><br>
    <i style="background:#B2FBA5; width:10px; height:10px; float:left; margin-right:5px;"></i> Bon<br>
    <i style="background:#FFF44F; width:10px; height:10px; float:left; margin-right:5px;"></i> Moyen<br>
    <i style="background:#F9AB59; width:10px; height:10px; float:left; margin-right:5px;"></i> Dégradé<br>
    <i style="background:#FF6961; width:10px; height:10px; float:left; margin-right:5px;"></i> Mauvais<br>
    <i style="background:#C3B1E1; width:10px; height:10px; float:left; margin-right:5px;"></i> Très mauvais<br>
    <i style="background:black; width:10px; height:10px; float:left; margin-right:5px;"></i> Extrêmement mauvais
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m._repr_html_()

# -----------------------------
# UI COMPONENTS
# -----------------------------
def display_atmo_card(atmo_data, poll_dom, val_dom):
    if not atmo_data.empty:
        atmo = atmo_data.iloc[0]
        couleur_atmo = atmo["couleur_qualite"]
        libelle_atmo = atmo["libelle_qualite"]
        indice_atmo = atmo["indice_qualite_air"]
        recommandation = RECOMMANDATIONS_ATMO.get(libelle_atmo, "Pas de recommandation disponible pour ce niveau.")
        
        st.markdown(f"""
        <div style="background-color: {couleur_atmo}; padding: 15px; border-radius: 8px; color: black; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin: 0; color: black; font-weight: bold;">Indice Atmo : {indice_atmo}</h3>
            <h4 style="margin: 0; color: black;">({libelle_atmo})</h4>
        </div>
        <div style="background-color: {CARD_BACKGROUND}; padding: 15px; border-radius: 8px; margin-top: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #E7ECF6;">
            <p style="margin: 0; font-size: 0.9rem;">{recommandation}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if poll_dom and val_dom:
            st.markdown(f"<p style='text-align:center; margin-top:10px;'>Polluant dominant : <strong>{poll_dom}</strong> ({val_dom} µg/m³)</p>", unsafe_allow_html=True)

    else:
        st.info("Données Atmo non disponibles.")

def display_meteo_card(meteo_data):
    if not meteo_data.empty:
        meteo_info = meteo_data.iloc[0]
        st.markdown(f"""
        <div class="kpi" style="display: flex; justify-content: space-around; text-align: center; background-color: #fff; padding: 16px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div>
                <p style="margin: 0; font-size: 0.9rem;">Température</p>
                <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">☀️ {meteo_info['temperature_2m']:.1f}°C</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.9rem;">Vent</p>
                <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">💨 {meteo_info['windspeed_10m']:.1f} km/h</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 0.9rem;">Humidité</p>
                <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">💧 {meteo_info['relative_humidity_2m']:.0f}%</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Pas de données météo disponibles pour l'heure et la date sélectionnées.")

def display_pollen_card(pollen_row, jours_fr):
    niveau = pollen_row["niveau_risque"]
    libelle = POLLEN_NIVEAUX.get(niveau, {}).get('libelle', 'Inconnu')
    couleur = POLLEN_NIVEAUX.get(niveau, {}).get('couleur', 'gray')
    recommandation = RECOMMANDATIONS_POLLEN.get(niveau, "Pas de recommandation.")
    jour_semaine = jours_fr.get(pollen_row['date_echeance'].weekday(), '---')

    st.markdown(f"""
    <div style="padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center; background-color: {couleur}80; border-left: 5px solid {couleur};">
        <p style="margin-bottom: 5px; font-weight: bold;">🍃 {jour_semaine} {pollen_row['date_echeance'].day}</p>
        <h4 style="color:{couleur}; margin: 0; font-weight: bold;">{libelle}</h4>
        <p style="font-size: 0.9rem; margin: 0;">({pollen_row['pollen_resp']})</p>
        <p style="font-size: 0.8rem; margin-top: 10px; color: #555;">{recommandation}</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# UI – STYLING
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');

    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(180deg, #E3F2FD 0%, #d1f0e1 100%) !important;
    }
    
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    .title-container {
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 30px;
    }

    .title {
        font-weight: 700; font-size: 32px; color: #2D3748;
        margin: 0;
    }

    .subtitle-header {
        font-weight: 400; font-size: 16px; color: #4A5568;
        margin-top: 5px;
    }

    .section-subtitle {
        font-weight: 600; font-size: 18px; color: #3B5998;
        border-bottom: 3px solid #A7C7E7;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }

    .softcard {
        padding: 16px; border-radius: 14px;
        background: #FFFFFFAA;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }

    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-weight: 700; font-size: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# EN-TÊTE DU TABLEAU DE BORD
# -----------------------------
st.markdown(
    """
    <style>
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 20px;
        background: #ffffffcc;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    .titles-container {
        flex-grow: 1;
        text-align: center;
    }
    .main-title {
        font-size: 2.5em; /* Agrandissement du titre */
        font-weight: 700;
        color: #2D3748;
        margin: 0;
    }
    .sub-title {
        font-size: 1.2em;
        color: #4A5568;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="header-container">', unsafe_allow_html=True)

# Logo
st.image(
    "/Users/yasmine/Documents/projet-data-QA-1/image.png",
    width=150, # Ajuste la taille du logo
)

# Titre et sous-titre
st.markdown(
    """
    <div class="titles-container">
        <h1 class="main-title">Tableau de Bord – Qualité de l’air en Région Sud</h1>
        <p class="sub-title">Projet Data – Région Provence-Alpes-Côte d’Azur</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# DATE & FILTRES
# -----------------------------
st.markdown(f"**Date du jour :** {dt.date.today().strftime('%d %B %Y')}")

col_ville_header, col_tabs = st.columns([1, 2])
with col_ville_header:
    ville_choisie = st.selectbox("Ville ou zone", list(VILLES.keys()))

tab1, tab2 = st.tabs(["Vue d'ensemble", "Analyse"])
# -----------------------------
# PAGE 1 – VUE D’ENSEMBLE
# -----------------------------
with tab1:
    insee = VILLES[ville_choisie]["insee"]
    dept_code = VILLES[ville_choisie]["dept_code"]
    
    col_map, col_indicateurs = st.columns([0.7, 0.3])
    
    with col_map:
        st.markdown('<div class="softcard">', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Carte des stations de mesure</p>', unsafe_allow_html=True)
        polluant_carte = st.selectbox("Polluant à afficher", POLLUANTS, key="polluant_carte")
        mesures_courantes = get_mesures_courantes_by_ville_polluant(ville_choisie, polluant_carte)
        if not mesures_courantes.empty:
            folium_map_html = generate_folium_map(mesures_courantes, ville_choisie)
            components.html(folium_map_html, height=1000)
        else:
            st.info(f"Pas de données de mesure disponibles pour le polluant {polluant_carte}.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_indicateurs:
        st.markdown('<div class="softcard">', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Indicateurs clés</p>', unsafe_allow_html=True)
        
        col_date, col_heure = st.columns(2)
        with col_date:
            date_select = st.date_input("Date", value=dt.date.today())
        with col_heure:
            time_select = st.select_slider("Heure", options=range(24), value=dt.datetime.now().hour)
        
        st.markdown('<p class="section-subtitle">Indice ATMO</p>', unsafe_allow_html=True)
        atmo_actuel = get_indice_atmo_by_date(insee, date_select)
        poll_dom, val_dom = get_polluant_dominant_du_jour(insee)
        display_atmo_card(atmo_actuel, poll_dom, val_dom)
        
        st.markdown('<br>', unsafe_allow_html=True)
        
        st.markdown('<p class="section-subtitle">Météo</p>', unsafe_allow_html=True)
        meteo_last = get_meteo_by_hour(ville_choisie, date_select, time_select)
        display_meteo_card(meteo_last)
            
        st.markdown('<br>', unsafe_allow_html=True)
        
        # NOUVEL ENCADRÉ AVEC L'ÉTAT ACTUEL DES POLLUANTS ET LES PRÉVISIONS POLLEN
        with st.container():
            st.markdown('<p class="section-subtitle">État actuel et prévisions</p>', unsafe_allow_html=True)
            st.markdown('<div class="softcard">', unsafe_allow_html=True)
            
            # --- État actuel des polluants ---
            st.markdown('<p style="font-weight: bold; font-size: 1rem; color: #3B5998;">Concentrations moyennes actuelles</p>', unsafe_allow_html=True)
            
            polluants_affiches = ['NO2', 'PM10', 'O3'] # Liste des polluants à afficher
            df_actuel = get_mesures_actuelles_tous_polluants(ville_choisie, polluants_affiches)
            
            if not df_actuel.empty:
                col_polluants = st.columns(len(polluants_affiches))
                for i, (_, row) in enumerate(df_actuel.iterrows()):
                    polluant = row['polluant']
                    valeur = row['valeur_moyenne']
                    seuil = SEUILS.get(polluant, None)
                    
                    couleur_valeur = "#3B5998" # Couleur par défaut
                    if seuil is not None:
                        if valeur > seuil:
                            couleur_valeur = ALERT
                        elif valeur > seuil * 0.7:
                            couleur_valeur = WARN
                        else:
                            couleur_valeur = SUCCESS
                    
                    with col_polluants[i]:
                        st.markdown(f"""
                        <div style="text-align: center; border-radius: 8px; padding: 10px; background-color: #f9f9f9; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                            <p style="margin: 0; font-size: 0.9rem; font-weight: bold;">{polluant}</p>
                            <h4 style="margin: 0; color: {couleur_valeur}; font-weight: bold;">{valeur:.1f}</h4>
                            <p style="margin: 0; font-size: 0.8rem; color: #555;">µg/m³</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Aucune donnée actuelle disponible pour les polluants sélectionnés.")
            
            st.markdown('<br>', unsafe_allow_html=True)
            
            # --- Prévisions Pollen ---
            st.markdown('<p style="font-weight: bold; font-size: 1rem; color: #3B5998;">Prévisions Risque Pollen</p>', unsafe_allow_html=True)
            previsions_pollen = get_prevision_pollen_ville(insee)
            if not previsions_pollen.empty:
                cols_pollen = st.columns(3)
                jours_fr = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Jeu", 4: "Ven", 5: "Sam", 6: "Dim"}
                for i, row in previsions_pollen.iterrows():
                    with cols_pollen[i]:
                        display_pollen_card(row, jours_fr)
            else:
                st.info("Pas de prévisions de pollen disponibles.")

            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    
    col_chart_emissions_ges, col_chart_emissions_polluant = st.columns([1, 2])
    
    with col_chart_emissions_ges:
        st.markdown('<div class="softcard">', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Répartition des émissions par secteur - Région PACA</p>', unsafe_allow_html=True)
        emissions_donut = get_emissions_par_secteur_paca()
        if not emissions_donut.empty:
            fig_donut = px.pie(emissions_donut, names="secteur", values="total_ges", hole=0.5, color_discrete_sequence=PALETTE_PASTEL)
            fig_donut.update_traces(textinfo='percent+label')
            fig_donut.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), height=350)
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Pas de données d’émission pour la région PACA.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_chart_emissions_polluant:
        st.markdown('<div class="softcard">', unsafe_allow_html=True)
        st.markdown(f'<p class="section-subtitle">Émissions par secteur et par polluant (2025 - PACA)</p>', unsafe_allow_html=True)
        emissions_bar = get_emissions_by_sector_pollutant()

        if not emissions_bar.empty:
            fig_bar = px.bar(emissions_bar, x='secteur', y='quantite', color='polluant', barmode='group',
                             labels={"quantite": "Émissions (tonnes/an)", "secteur": "Secteur d'activité"},
                             color_discrete_map={'PM25': PALETTE_PASTEL[0], 'PM10': PALETTE_PASTEL[1], 'NOx': PALETTE_PASTEL[2]})
            fig_bar.update_layout(plot_bgcolor="white", height=350, legend_title_text='Polluant', xaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Pas de données d'émissions par secteur et polluant.")
        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------
    # NOUVEAU GRAPHIQUE DE COMPARAISON
    # -----------------------------
    st.markdown('<div class="softcard">', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Comparaison de la qualité de l\'air par ville (NO₂)</p>', unsafe_allow_html=True)

    df_comparaison = get_comparaison_inter_villes(polluant='NO2')

    if not df_comparaison.empty:
        fig_bar = px.bar(
            df_comparaison,
            x='ville',
            y='valeur_moyenne',
            color='ville',
            labels={'valeur_moyenne': 'Moyenne NO₂ (µg/m³)'},
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig_bar.update_layout(
            xaxis_title=None,
            yaxis_title="Concentration moyenne (µg/m³)",
            showlegend=False,
            plot_bgcolor="white",
            height=350
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Pas de données disponibles pour la comparaison inter-villes.")

    st.markdown('</div>', unsafe_allow_html=True)

    
# -----------------------------
# PAGE 2 – ANALYSE
# -----------------------------
with tab2:
    st.markdown('<div class="softcard">', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Analyse détaillée</p>', unsafe_allow_html=True)
    col_polluant_select, col_period_select = st.columns(2)
    with col_polluant_select:
        polluant_select = st.selectbox("Sélectionner un polluant", POLLUANTS, key="analyse_polluant")
    with col_period_select:
        periode = st.select_slider(
            "Période d'analyse",
            options=[7, 14, 30],
            value=7,
            format_func=lambda x: f"{x} jours glissants"
        )
        periode_fin = dt.date.today()
        periode_debut = periode_fin - dt.timedelta(days=periode)

    df_series = get_series_pollution_par_heure(ville_choisie, polluant_select, periode_debut, periode_fin)
    
    if not df_series.empty:
        fig_series = px.line(df_series, x="heure", y="valeur_moyenne", title=f"Évolution horaire de {polluant_select} à {ville_choisie}",
                             color_discrete_sequence=[PRIMARY])
        fig_series.add_hline(y=SEUILS.get(polluant_select, 0), line_dash="dash", line_color="red", annotation_text=f"Seuil de {polluant_select}", annotation_position="top left")
        fig_series.update_layout(
            plot_bgcolor="white",
            xaxis_title="Heure",
            yaxis_title="Concentration (µg/m³)",
            hovermode="x unified",
            height=400
        )
        st.plotly_chart(fig_series, use_container_width=True)
    else:
        st.info(f"Pas de données horaires pour {polluant_select} sur la période sélectionnée.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # -----------------------------
    # CORRELATION
    # -----------------------------
    st.markdown('<div class="softcard">', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Corrélation Pollution / Trafic et Météo</p>', unsafe_allow_html=True)

    df_correlation = get_all_correlation_data(ville_choisie, periode_debut, periode_fin)
    
    if not df_correlation.empty:
        col_corr1, col_corr2 = st.columns(2)

        with col_corr1:
            fig_corr = px.scatter(
                df_correlation,
                x='trafic',
                y='NO2',
                trendline="ols",
                title=f"Corrélation NO₂ vs Trafic"
            )
            fig_corr.update_layout(plot_bgcolor="white", xaxis_title="Trafic (véhicules/heure)", yaxis_title="NO₂ (µg/m³)")
            st.plotly_chart(fig_corr, use_container_width=True)

        with col_corr2:
            fig_temp_corr = px.scatter(
                df_correlation,
                x='temperature_2m',
                y='O3',
                trendline="ols",
                title=f"Corrélation O₃ vs Température"
            )
            fig_temp_corr.update_layout(plot_bgcolor="white", xaxis_title="Température (°C)", yaxis_title="O₃ (µg/m³)")
            st.plotly_chart(fig_temp_corr, use_container_width=True)
            
        with st.expander("Voir les coefficients de corrélation"):
            df_corr = df_correlation.corr(numeric_only=True)
            st.dataframe(df_corr.style.background_gradient(cmap='RdYlGn', axis=None, vmin=-1, vmax=1), use_container_width=True)
    else:
        st.info("Pas de données disponibles pour l'analyse de corrélation.")
    
    st.markdown('</div>', unsafe_allow_html=True)