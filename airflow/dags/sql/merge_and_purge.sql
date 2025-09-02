BEGIN;

-- 1. Nettoyage du staging
TRUNCATE staging.mesure_journaliere;
TRUNCATE staging.indice_atmo;
TRUNCATE staging.indice_pollen;
TRUNCATE staging.meteo;
TRUNCATE staging.emission_par_secteur;
TRUNCATE staging.episode_3_j;

-- 2. Chargement des fichiers CSV vers le staging
COPY staging.mesure_journaliere(
  id_station, code_station, nom_station, adresse, polluant,
  datetime, code_polluant, longitude, latitude, valeur,
  code_indice, couleur_indice, qualificatif, date, heure
)
FROM '/data/clean/mesure_journaliere_clean.csv'
DELIMITER ',' CSV HEADER ENCODING 'UTF8';

COPY staging.indice_atmo(
  code_insee, date_echeance, indice_no2, indice_o3, indice_pm10,
  indice_pm25, indice_qualite_air, couleur_qualite,
  date_diffusion, date_mise_a_jour, libelle_qualite,
  type_zone, lon, lat
)
FROM '/data/clean/indices_atmo_clean.csv'
DELIMITER ';' CSV HEADER ENCODING 'UTF8';

COPY staging.indice_pollen(
  code_insee, date_echeance, alerte,
  code_ambr, code_arm, code_aul, code_boul, code_gram, code_oliv,
  conc_ambr, conc_arm, conc_aul, conc_boul, conc_gram, conc_oliv,
  pollen_resp, source
)
FROM '/data/clean/indices_pollens_clean.csv'
DELIMITER ',' CSV HEADER ENCODING 'UTF8';

COPY staging.meteo(
  time, temperature_2m, relative_humidity_2m,
  precipitation, windspeed_10m, ville
)
FROM '/data/clean/meteo_clean.csv'
DELIMITER ',' CSV HEADER ENCODING 'UTF8';

COPY staging.emission_par_secteur(
  region, date_maj, superficie, population,
  pm25, pm10, nox, ges, code_pcaet, code
)
FROM '/data/clean/emissions_par_secteur_clean.csv'
DELIMITER ',' CSV HEADER ENCODING 'UTF8';

COPY staging.episode_3_j(
  code_zone, code_pol, lib_pol, date_echeance, etat
)
FROM '/data/clean/episodes_3jours_clean.csv'
DELIMITER ',' CSV HEADER ENCODING 'UTF8';

-- 3. Merge dans prod avec gestion des doublons

-- Mesures journalières
INSERT INTO prod.mesure_journaliere
SELECT * FROM staging.mesure_journaliere
ON CONFLICT (id_station, datetime, polluant)
DO UPDATE SET
  code_station   = EXCLUDED.code_station,
  nom_station    = EXCLUDED.nom_station,
  adresse        = EXCLUDED.adresse,
  code_polluant  = EXCLUDED.code_polluant,
  longitude      = EXCLUDED.longitude,
  latitude       = EXCLUDED.latitude,
  valeur         = EXCLUDED.valeur,
  code_indice    = EXCLUDED.code_indice,
  couleur_indice = EXCLUDED.couleur_indice,
  qualificatif   = EXCLUDED.qualificatif,
  date           = EXCLUDED.date,
  heure          = EXCLUDED.heure;

-- Indice Atmo
INSERT INTO prod.indice_atmo
SELECT * FROM staging.indice_atmo
ON CONFLICT (code_insee, date_echeance)
DO UPDATE SET
  indice_no2         = EXCLUDED.indice_no2,
  indice_o3          = EXCLUDED.indice_o3,
  indice_pm10        = EXCLUDED.indice_pm10,
  indice_pm25        = EXCLUDED.indice_pm25,
  indice_qualite_air = EXCLUDED.indice_qualite_air,
  couleur_qualite    = EXCLUDED.couleur_qualite,
  date_diffusion     = EXCLUDED.date_diffusion,
  date_mise_a_jour   = EXCLUDED.date_mise_a_jour,
  libelle_qualite    = EXCLUDED.libelle_qualite,
  type_zone          = EXCLUDED.type_zone,
  lon                = EXCLUDED.lon,
  lat                = EXCLUDED.lat;

-- Indice Pollen
INSERT INTO prod.indice_pollen
SELECT * FROM staging.indice_pollen
ON CONFLICT (code_insee, date_echeance)
DO UPDATE SET
  alerte      = EXCLUDED.alerte,
  code_ambr   = EXCLUDED.code_ambr,
  code_arm    = EXCLUDED.code_arm,
  code_aul    = EXCLUDED.code_aul,
  code_boul   = EXCLUDED.code_boul,
  code_gram   = EXCLUDED.code_gram,
  code_oliv   = EXCLUDED.code_oliv,
  conc_ambr   = EXCLUDED.conc_ambr,
  conc_arm    = EXCLUDED.conc_arm,
  conc_aul    = EXCLUDED.conc_aul,
  conc_boul   = EXCLUDED.conc_boul,
  conc_gram   = EXCLUDED.conc_gram,
  conc_oliv   = EXCLUDED.conc_oliv,
  pollen_resp = EXCLUDED.pollen_resp,
  source      = EXCLUDED.source;

-- Météo
INSERT INTO prod.meteo
SELECT * FROM staging.meteo
ON CONFLICT (ville, time)
DO UPDATE SET
  temperature_2m       = EXCLUDED.temperature_2m,
  relative_humidity_2m = EXCLUDED.relative_humidity_2m,
  precipitation        = EXCLUDED.precipitation,
  windspeed_10m        = EXCLUDED.windspeed_10m;

-- Émissions par secteur (on garde historique, donc on évite le conflit)
INSERT INTO prod.emission_par_secteur
SELECT * FROM staging.emission_par_secteur
ON CONFLICT DO NOTHING;

-- Épisodes 3 jours
INSERT INTO prod.episode_3_j
SELECT * FROM staging.episode_3_j
ON CONFLICT (code_zone, code_pol, date_echeance)
DO UPDATE SET
  lib_pol = EXCLUDED.lib_pol,
  etat    = EXCLUDED.etat;

-- 4. Purge des données anciennes (dans prod)
DELETE FROM prod.mesure_journaliere WHERE datetime < NOW() - INTERVAL '7 days';
DELETE FROM prod.meteo              WHERE time < NOW() - INTERVAL '7 days';
DELETE FROM prod.indice_atmo        WHERE date_echeance < CURRENT_DATE - INTERVAL '7 days';
DELETE FROM prod.indice_pollen      WHERE date_echeance < CURRENT_DATE - INTERVAL '7 days';

COMMIT;
