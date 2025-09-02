from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
import sys

# Accès aux scripts
sys.path.append("/opt/airflow/scripts")

# === Import des fonctions de collecte ===
from collecte import (
    authentifier,
    collect_indices_atmo,
    collect_meteo_open_meteo,
    collect_episodes,
    collect_pollens,
    collect_mesures_horaires_atmosud,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="collecte_temps_reel",
    description="DAG de collecte automatique (indices, météo, mesures horaires)",
    schedule_interval="@daily",           # OK si tu veux aussi un run auto chaque jour
    start_date=datetime(2025, 8, 1),
    catchup=False,
    default_args=default_args,
    tags=["qa", "etl", "collecte"],
) as dag:

    # Wrappers pour gérer l'auth Atmo Sud
    def wrapper_indices_atmo():
        headers = authentifier()
        collect_indices_atmo(headers)

    def wrapper_episodes_pollution():
        headers = authentifier()
        collect_episodes(headers)

    def wrapper_pollens():
        headers = authentifier()
        collect_pollens(headers)

    task_collect_indices = PythonOperator(
        task_id="collect_indices_atmo",
        python_callable=wrapper_indices_atmo,
    )

    task_collect_episodes = PythonOperator(
        task_id="collect_episodes_pollution",
        python_callable=wrapper_episodes_pollution,
    )

    task_collect_pollens = PythonOperator(
        task_id="collect_pollens",
        python_callable=wrapper_pollens,
    )

    task_collect_meteo = PythonOperator(
        task_id="collect_meteo",
        python_callable=collect_meteo_open_meteo,
    )

    task_collect_mesures = PythonOperator(
        task_id="collect_mesures_horaires",
        python_callable=collect_mesures_horaires_atmosud,
    )

    # === Déclenchement du DAG de transform/chargement à la fin de TOUTE la collecte ===
    trigger_transform = TriggerDagRunOperator(
        task_id="trigger_transform_load_daily",
        trigger_dag_id="transform_load_daily",
        wait_for_completion=False,   # mets True si tu veux attendre la fin du DAG suivant
        reset_dag_run=True,          # évite les collisions si un run existe déjà au même logical_date
    )

    # Les 5 tâches de collecte peuvent tourner en parallèle, puis on déclenche le transform
    [task_collect_indices,
     task_collect_episodes,
     task_collect_pollens,
     task_collect_meteo,
     task_collect_mesures] >> trigger_transform
