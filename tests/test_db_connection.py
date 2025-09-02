import os
import psycopg2
import pytest

def test_postgres_mesure_journaliere():
    """
    Vérifie que la base PostgreSQL QualAir est accessible
    et que la table prod.mesure_journaliere contient au moins 1 enregistrement.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "qualair_db")
    db_user = os.getenv("DB_USER", "yasminedri")
    db_pass = os.getenv("DB_PASS", "qualair")

    try:
        # Connexion à PostgreSQL
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass,
            connect_timeout=5
        )
        cur = conn.cursor()

        # Vérifie que la table existe et contient des données
        cur.execute("SELECT COUNT(*) FROM prod.mesure_journaliere;")
        result = cur.fetchone()

        assert result is not None, "La table prod.mesure_journaliere n'existe pas"
        assert result[0] > 0, "La table prod.mesure_journaliere est vide"

        conn.close()

    except Exception as e:
        pytest.fail(f"Connexion PostgreSQL ou test sur prod.mesure_journaliere échoué: {e}")
