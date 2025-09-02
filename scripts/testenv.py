import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

# Charger le .env
load_dotenv()

# Récupérer les variables
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGDB   = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASS = os.getenv("PGPASSWORD")

# Créer l'URL de connexion SQLAlchemy
DB_URL = f"postgresql+psycopg2://{PGUSER}:{PGPASS}@{PGHOST}:{PGPORT}/{PGDB}"
engine = create_engine(DB_URL, pool_pre_ping=True)

# Tester la connexion
try:
    with engine.connect() as con:
        df = pd.read_sql(text("SELECT CURRENT_DATE AS today, CURRENT_USER AS user, current_database() AS db;"), con)
    print("✅ Connexion réussie !")
    print(df)
except Exception as e:
    print("❌ Erreur de connexion :", e)
