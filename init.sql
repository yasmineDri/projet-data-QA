-- =============================================
-- Table mesures_journaliere
-- =============================================
DROP TABLE IF EXISTS mesures_journaliere;

CREATE TABLE mesures_polluants (
    date_debut TIMESTAMP WITH TIME ZONE NOT NULL,
    valeur FLOAT NOT NULL,
    unite TEXT NOT NULL,
    nom_station TEXT NOT NULL,
    id_station TEXT NOT NULL,
    label_polluant TEXT NOT NULL,
    polluant_id INTEGER NOT NULL,
    temporalite TEXT NOT NULL,
    validation TEXT,
    PRIMARY KEY (date_debut, id_station, polluant_id)
);

CREATE INDEX idx_mesures_polluants_station ON mesures_polluants (id_station);

-- =============================================
-- Table indices_atmo
-- =============================================
DROP TABLE IF EXISTS indices_atmo;

CREATE TABLE indices_atmo (
    aasqa INTEGER NOT NULL,
    date_maj TIMESTAMP WITH TIME ZONE NOT NULL,
    code_no2 INTEGER NOT NULL,
    code_o3 INTEGER NOT NULL,
    code_pm10 INTEGER NOT NULL,
    code_pm25 FLOAT NOT NULL,
    code_qual INTEGER NOT NULL,
    code_so2 INTEGER NOT NULL,
    code_zone INTEGER NOT NULL,
    coul_qual TEXT NOT NULL,
    date_dif DATE NOT NULL,
    date_ech DATE NOT NULL,
    epsg_reg INTEGER,
    lib_qual TEXT NOT NULL,
    lib_zone TEXT NOT NULL,
    source TEXT NOT NULL,
    type_zone TEXT NOT NULL,
    x_reg FLOAT,
    x_wgs84 FLOAT,
    y_reg FLOAT,
    y_wgs84 FLOAT,
    gml_id2 TEXT,
    PRIMARY KEY (aasqa, date_maj, code_zone)
);

-- =============================================
-- Table indices_pollens
-- =============================================
DROP TABLE IF EXISTS indices_pollens;

CREATE TABLE indices_pollens (
    aasqa INTEGER NOT NULL,
    date_maj TIMESTAMP WITH TIME ZONE NOT NULL,
    alerte INTEGER,
    code_ambr INTEGER,
    code_arm INTEGER,
    code_aul INTEGER,
    code_boul INTEGER,
    code_gram INTEGER,
    code_oliv INTEGER,
    code_zone INTEGER NOT NULL,
    conc_ambr FLOAT,
    conc_arm FLOAT,
    conc_aul FLOAT,
    conc_boul FLOAT,
    conc_gram FLOAT,
    conc_oliv FLOAT,
    date_dif DATE,
    date_ech DATE,
    lib_qual TEXT,
    lib_zone TEXT NOT NULL,
    type_zone TEXT,
    pollen_resp TEXT,
    source TEXT,
    code_qual INTEGER,
    name TEXT,
    PRIMARY KEY (aasqa, date_maj, code_zone)
);

-- =============================================
-- Table emissions_par_secteur
-- =============================================
DROP TABLE IF EXISTS emissions_par_secteur;

CREATE TABLE emissions_par_secteur (
    name TEXT NOT NULL,
    annee INTEGER NOT NULL,
    lib_commune TEXT NOT NULL,
    code_commune TEXT NOT NULL,
    polluant TEXT NOT NULL,
    valeur FLOAT NOT NULL,
    unite TEXT NOT NULL,
    lib_secteur TEXT NOT NULL,
    code_secteur INTEGER NOT NULL,
    PRIMARY KEY (name, annee, code_commune, polluant)
);

CREATE INDEX idx_emissions_secteur ON emissions_par_secteur (lib_secteur);

-- =============================================
-- Table episodes_3jours
-- =============================================
DROP TABLE IF EXISTS episodes_3jours;

CREATE TABLE episodes_3jours (
    aasqa INTEGER NOT NULL,
    date_maj TIMESTAMP WITH TIME ZONE NOT NULL,
    etat TEXT NOT NULL,
    lib_zone TEXT NOT NULL,
    lib_pol TEXT NOT NULL,
    date_ech DATE NOT NULL,
    date_dif DATE NOT NULL,
    code_zone INTEGER NOT NULL,
    code_pol INTEGER NOT NULL,
    PRIMARY KEY (aasqa, date_maj, code_zone, code_pol)
);

CREATE INDEX idx_episodes_zone ON episodes_3jours (code_zone);
