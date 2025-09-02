from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.exceptions import AirflowException
from datetime import timedelta
import pendulum, os, sys

# Accès aux scripts
sys.path.append("/opt/airflow/scripts")
from transform_all import run_all_transforms

DATA_DIR = os.environ.get("AIRFLOW_DATA_DIR", "/opt/airflow/data")
CLEAN = os.path.join(DATA_DIR, "clean")

local_tz = pendulum.timezone("Europe/Paris")

def check_non_empty(filepath: str):
    """Fail si fichier manquant ou sans données (header seul)."""
    if not os.path.exists(filepath):
        raise AirflowException(f"Fichier introuvable: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        for i, _ in enumerate(f, start=1):
            if i >= 2:
                break
    if i < 2:
        raise AirflowException(f"Fichier vide: {filepath}")
    return filepath

default_args = {"owner": "airflow", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="transform_load_daily",
    description="Transformations + chargement Postgres après la collecte",
    # Laissez None si vous déclenchez ce DAG via TriggerDagRun depuis 'collecte_temps_reel'
    schedule_interval=None,
    start_date=local_tz.datetime(2025, 8, 1, 1, 0),
    catchup=False,
    default_args=default_args,
    tags=["qa", "etl"],
) as dag:

    # Transform: génère les *_clean.csv dans /opt/airflow/data/clean
    t_transform = PythonOperator(
        task_id="transform_all",
        python_callable=run_all_transforms,
        retries=2,
        retry_exponential_backoff=True,
        execution_timeout=timedelta(minutes=20),
    )

    # Checks: empêche de charger des fichiers vides
    files = [
        "mesure_journaliere_clean.csv",
        "indices_atmo_clean.csv",
        "indices_pollens_clean.csv",
        "meteo_clean.csv",
        "emissions_par_secteur_clean.csv",
        "episodes_3jours_clean.csv",
        # "trafic_synthetique_clean.csv",
    ]
    checks = [
        PythonOperator(
            task_id=f"check_{f.split('_clean')[0]}",
            python_callable=check_non_empty,
            op_kwargs={"filepath": os.path.join(CLEAN, f)},
        )
        for f in files
    ]

    # Load Postgres : COPY staging -> UPSERT -> purge 7j
    t_load = PostgresOperator(
        task_id="merge_and_purge",
        postgres_conn_id="pg_main",
        sql="sql/merge_and_purge.sql",
    )

    # Dépendances
    t_transform >> checks >> t_load
