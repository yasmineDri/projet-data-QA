-- =============================================
-- Table ville
-- =============================================
DROP TABLE IF EXISTS ville;

CREATE TABLE ville (
    id_ville SERIAL PRIMARY KEY,
    code_insee VARCHAR(10) UNIQUE NOT NULL,
    nom_commune TEXT NOT NULL,
    lon FLOAT NOT NULL,
    lat FLOAT NOT NULL
);

-- =============================================
-- Table station
-- =============================================
DROP TABLE IF EXISTS station;

CREATE TABLE station (
    id_station INTEGER PRIMARY KEY,
    nom_station TEXT NOT NULL,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    code_insee VARCHAR(10) NOT NULL,
    FOREIGN KEY (code_insee) REFERENCES ville(code_insee)
);

DROP TABLE IF EXISTS mesure_journaliere;

CREATE TABLE mesure_journaliere (
    id_station INTEGER NOT NULL,
    code_station TEXT NOT NULL,
    nom_station TEXT NOT NULL,
    adresse TEXT,
    polluant TEXT NOT NULL,
    datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    code_polluant INTEGER NOT NULL,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    valeur FLOAT,
    code_indice FLOAT,
    couleur_indice TEXT,
    qualificatif TEXT,
    date TEXT NOT NULL,
    heure TEXT NOT NULL,
    PRIMARY KEY (id_station, datetime, polluant)
);


-- =============================================
-- Table indice_atmo
-- =============================================
DROP TABLE IF EXISTS indice_atmo;

CREATE TABLE indice_atmo (
    code_insee VARCHAR(10) NOT NULL,
    date_echeance DATE NOT NULL,
    indice_no2 INTEGER,
    indice_o3 INTEGER,
    indice_pm10 INTEGER,
    indice_pm25 FLOAT,
    indice_qualite_air INTEGER,
    couleur_qualite TEXT,
    date_diffusion DATE,
    date_mise_a_jour TIMESTAMP WITH TIME ZONE,
    libelle_qualite TEXT,
    type_zone TEXT,
    lon FLOAT,
    lat FLOAT,
    PRIMARY KEY (code_insee, date_echeance),
    FOREIGN KEY (code_insee) REFERENCES ville(code_insee)
);

-- =============================================
-- Table indice_pollen
-- =============================================
DROP TABLE IF EXISTS indice_pollen;

CREATE TABLE indice_pollen (
    code_insee VARCHAR(10) NOT NULL,
    date_echeance DATE NOT NULL,
    alerte INTEGER,
    code_ambr INTEGER,
    code_arm INTEGER,
    code_aul INTEGER,
    code_boul INTEGER,
    code_gram INTEGER,
    code_oliv INTEGER,
    conc_ambr FLOAT,
    conc_arm FLOAT,
    conc_aul FLOAT,
    conc_boul FLOAT,
    conc_gram FLOAT,
    conc_oliv FLOAT,
    pollen_resp TEXT,
    source TEXT,
    PRIMARY KEY (code_insee, date_echeance),
    FOREIGN KEY (code_insee) REFERENCES ville(code_insee)
);


-- =============================================
-- Table trafic_synthetique
-- =============================================
DROP TABLE IF EXISTS trafic_synthetique;

CREATE TABLE trafic_synthetique (
    ville TEXT NOT NULL,
    date DATE NOT NULL,
    heure TIME NOT NULL,
    trafic FLOAT NOT NULL,
    PRIMARY KEY (ville, date, heure)
);

-- =============================================
-- Table meteo
-- =============================================
DROP TABLE IF EXISTS meteo;

CREATE TABLE meteo (
    ville TEXT NOT NULL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    temperature_2m FLOAT,
    relative_humidity_2m FLOAT,
    precipitation FLOAT,
    windspeed_10m FLOAT,
    PRIMARY KEY (ville, time)
);

-- =============================================
-- Table emission_par_secteur
-- =============================================
DROP TABLE IF EXISTS emission_par_secteur;

CREATE TABLE emission_par_secteur (
    region TEXT NOT NULL,
    date_maj DATE,
    superficie FLOAT,
    population INTEGER,
    pm25 FLOAT,
    pm10 FLOAT,
    nox FLOAT,
    ges FLOAT,
    code_pcaet TEXT,
    code TEXT,
);

-- =============================================
-- Table episode_3_j
-- =============================================
DROP TABLE IF EXISTS episode_3_j;

CREATE TABLE episode_3_j (
    code_zone VARCHAR(5) NOT NULL,
    code_pol INTEGER NOT NULL,
    lib_pol TEXT,
    date_echeance DATE NOT NULL,
    etat TEXT,
    PRIMARY KEY (code_zone, code_pol, date_echeance)
);
