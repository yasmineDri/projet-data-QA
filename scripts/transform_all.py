import pandas as pd
from pathlib import Path
from clean import (
    clean_indices_atmo,
    clean_emissions_par_secteur,
    clean_indices_pollens,
    clean_episodes_3jours,
    clean_mesures,
    clean_meteo,
)

# --- Chemins de base ---
import os
BASE = Path(os.environ.get("AIRFLOW_DATA_DIR", "/data"))
RAW = BASE / "raw"
RAW_ATMO = RAW / "atmo"
RAW_METEO = RAW / "meteo"
CLEAN = BASE / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)

# --- Utilitaires ---
def count_dupes_mesures(df: pd.DataFrame) -> int:
    if {"id_station", "datetime", "polluant"}.issubset(df.columns):
        return int(df.duplicated(subset=["id_station", "datetime", "polluant"]).sum())
    return 0

def run_one(name, src_path, sep_in, pre_fn, cleaner, out_path, sep_out=","):
    if not src_path.exists():
        print(f"[SKIP] {name}: fichier absent -> {src_path}")
        return None
    try:
        raw = pd.read_csv(src_path, sep=sep_in, encoding="utf-8", engine="c")
    except Exception:
        try:
            raw = pd.read_csv(src_path, sep=None, encoding="utf-8", engine="python", on_bad_lines="skip")
        except Exception as e:
            print(f"[ERR ] {name}: lecture impossible {src_path} : {e}")
            return None

    try:
        raw = pre_fn(raw) if pre_fn else raw
    except Exception as e:
        print(f"[ERR ] {name}: pré-normalisation KO : {e}")
        return None

    before = len(raw)
    dup_before = count_dupes_mesures(raw)
    try:
        cleaned = cleaner(raw.copy())
    except Exception as e:
        print(f"[ERR ] {name}: nettoyage KO : {e}")
        return None

    after = len(cleaned)
    dup_after = count_dupes_mesures(cleaned)
    try:
        cleaned.to_csv(out_path, sep=sep_out, index=False, encoding="utf-8")
    except Exception as e:
        print(f".[ERR ] {name}: écriture KO {out_path} : {e}")
        return None

    print(f"[OK  ] {name}: {src_path.name} -> {out_path.name} | {before} -> {after} lignes")
    return {
        "dataset": name,
        "source": str(src_path).replace(str(BASE), "").lstrip("/"),
        "output": str(out_path.relative_to(BASE)),
        "rows_before": before,
        "rows_after": after,
        "removed": before - after,
        "dupes_before_mesures": dup_before,
        "dupes_after_mesures": dup_after,
    }

# --- Fonction principale ---
def main():
    summary = []
    jobs = [
        ("indices_atmo",
         RAW_ATMO / "indices_atmo.csv", ";",
         None, clean_indices_atmo,
         CLEAN / "indices_atmo_clean.csv", ";"),

        ("emissions_par_secteur",
         RAW_ATMO / "emissions_par_secteur.csv", ",",
         None, clean_emissions_par_secteur,
         CLEAN / "emissions_par_secteur_clean.csv", ","),

        ("indices_pollens",
         RAW_ATMO / "indices_pollens.csv", ";",
         None, clean_indices_pollens,
         CLEAN / "indices_pollens_clean.csv", ","),

        ("episodes_3jours",
         RAW_ATMO / "episodes_3jours.csv", ";",
         None, clean_episodes_3jours,
         CLEAN / "episodes_3jours_clean.csv", ","),

        ("mesure_journaliere",
         RAW_ATMO / "mesures_horaires_atmosud2.csv", ";",
         None, clean_mesures,
         CLEAN / "mesure_journaliere_clean.csv", ","),

        ("meteo",
         RAW_METEO / "meteo.csv", ";",
         None, clean_meteo,
         CLEAN / "meteo_clean.csv", ","),
    ]

    for name, src, sep_in, pre_fn, cleaner, out, sep_out in jobs:
        res = run_one(name, src, sep_in, pre_fn, cleaner, out, sep_out)
        if res:
            summary.append(res)

    if summary:
        rep = pd.DataFrame(summary, columns=[
            "dataset", "source", "output", "rows_before", "rows_after",
            "removed", "dupes_before_mesures", "dupes_after_mesures"
        ])
        rep.to_csv(CLEAN / "report_before_after.csv", index=False, encoding="utf-8")
        print(f"\nRésumé enregistré : {CLEAN / 'report_before_after.csv'}")
    else:
        print("Aucun dataset traité.")

# Fonction appelée par Airflow
def run_all_transforms():
    main()

if __name__ == "__main__":
    main()
