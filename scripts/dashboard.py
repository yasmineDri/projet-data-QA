import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# === Chargement des fichiers nettoyés ===
DATA_PATH = "./data"
df_mesures = pd.read_csv(f"{DATA_PATH}/mesure_journaliere_clean.csv", sep=";")
df_indices = pd.read_csv(f"{DATA_PATH}/indices_atmo_clean.csv", sep=",")
df_emissions = pd.read_csv(f"{DATA_PATH}/emissions_par_secteur_clean.csv", sep=",")
df_episodes = pd.read_csv(f"{DATA_PATH}/episodes_3jours_clean.csv", sep=",")
df_pollens = pd.read_csv(f"{DATA_PATH}/indices_pollens_clean.csv", sep=",")

# === Configuration Streamlit ===
st.set_page_config(page_title="Qualité de l'air en Région Sud", layout="wide")
st.title(" Tableau de bord - Qualité de l'air en Région Sud")

# === Sélection utilisateur ===
ville = st.selectbox("Sélectionnez une ville", sorted(df_indices["lib_zone"].dropna().unique()))
df_ville = df_indices[df_indices["lib_zone"] == ville]

# === Carte résumé dans colonne droite ===
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Carte des indices Atmo")
    date_disponibles = sorted(df_indices[df_indices["lib_zone"] == ville]["date_ech"].unique())
    date_selection = st.selectbox("Choisissez une date", date_disponibles[::-1])
    df_ville = df_indices[(df_indices["lib_zone"] == ville) & (df_indices["date_ech"] == date_selection)]
    fig_map = px.scatter_mapbox(
        df_ville,
        lat="y_wgs84",
        lon="x_wgs84",
        color="code_qual",
        size=[20] * len(df_ville),
        color_continuous_scale="RdYlGn_r",
        zoom=9,
        mapbox_style="carto-positron",
        hover_name="lib_zone"
    )
    fig_map.update_traces(marker=dict(sizemode="diameter", opacity=0.7))
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    last_row = df_ville.sort_values("date_ech", ascending=False).iloc[-1]
    polluants = {
        "NO2": last_row["code_no2"],
        "O3": last_row["code_o3"],
        "PM10": last_row["code_pm10"],
        "PM25": last_row["code_pm25"]
    }
    polluant_principal = max(polluants, key=polluants.get)
    score = last_row["code_qual"]
    qualite = last_row["lib_qual"]

    couleurs = {
        "Bon": "#50CCAA",
        "Moyen": "#F0E641",
        "Dégradé": "#FF9B57",
        "Mauvais": "#FF5050",
        "Très mauvais": "#960032",
        "Extrêmement mauvais": "#7E0023"
    }
    couleur = couleurs.get(qualite, "#999999")

    st.markdown(
        f"""
        <div style="background-color: {couleur}; padding: 1em 1.2em; border-radius: 10px;">
            <h3 style="margin: 0;">Indice : <strong>{score}</strong></h3>
            <p style="margin: 0;"><strong>{qualite}</strong></p>
            <hr style="margin: 5px 0;">
            <p style="margin: 0;">Polluant dominant : <strong>{polluant_principal}</strong></p>
        </div>
        """,
        unsafe_allow_html=True
    )

# === Sources d'émission (GES) ===
st.subheader("💨 Répartition des émissions de GES")
df_agg = df_emissions.groupby("code_pcaet")["ges"].sum().reset_index()
df_agg["code_pcaet"] = df_agg["code_pcaet"].replace({
    5: "Agriculture",
    6: "Transport routier",
    7: "Autres transports",
    34: "Résidentiel-Tertiaire",
    219: "Industrie"
})
fig_pie = px.pie(df_agg, values="ges", names="code_pcaet", title="GES par secteur d'activité")
st.plotly_chart(fig_pie, use_container_width=True)

# === Pollens ===
st.subheader("Indice pollinique")
df_pol = df_pollens[df_pollens["lib_zone"] == ville]
dernier_jour = df_pol["date_ech"].max()
df_pollens_today = df_pol[df_pol["date_ech"] == dernier_jour]

couleurs = {
    "Très bon": "#50CCAA",
    "Bon": "#A7D28D",
    "Moyen": "#F9E076",
    "Dégradé": "#F4A261",
    "Mauvais": "#F94144",
    "Très mauvais": "#9B2226",
    "Élevé": "#FF5050",
    "Modéré": "#F0E641",
    "Faible": "#50CCAA"
}
df_pollens_today["couleur"] = df_pollens_today["lib_qual"].map(couleurs)
fig_pol = px.bar(df_pollens_today,
                 x="pollen_resp",
                 y="conc_gram",
                 color="lib_qual",
                 color_discrete_map=couleurs,
                 title=f"Concentration en pollens ({dernier_jour})",
                 labels={"conc_gram": "Concentration (µg/m³)", "pollen_resp": "Type de pollen"})
st.plotly_chart(fig_pol)

# === Épisodes de pollution ===
st.subheader(" Épisodes de pollution (3 jours)")
df_ep = df_episodes[df_episodes["lib_zone"] == ville]
st.dataframe(df_ep[["lib_pol", "etat", "date_ech"]])

# === Footer ===
st.markdown("---")
st.markdown("Projet réalisé dans le cadre du M2 Ynov - Données : AtmoSud, Atmo-France")
