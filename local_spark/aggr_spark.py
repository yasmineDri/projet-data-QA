from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, avg, max as smax, count

# Crée la session Spark
spark = (SparkSession.builder
    .appName("AggrVilleJourPolluant")
    .master("local[*]")
    .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3")  # driver JDBC
    .getOrCreate())

# Connexion Postgres
jdbc_url = "jdbc:postgresql://localhost:5432/qualair_db"
props = {
    "user": "yasminedri",
    "password": "qualair",   # adapte si ton mdp est différent
    "driver": "org.postgresql.Driver"
}

# Lecture des mesures
df_mes = spark.read.jdbc(url=jdbc_url, table="prod.mesure_journaliere", properties=props)

# Lecture des stations
df_sta = spark.read.jdbc(url=jdbc_url, table="prod.station", properties=props)

print("Nb lignes mesures :", df_mes.count())
print("Nb lignes stations :", df_sta.count())

# Jointure
df = df_mes.join(df_sta, "id_station", "inner")
print("Nb lignes jointure :", df.count())
df.show(5, truncate=False)

# Agrégation par jour, ville, polluant
out = (df.withColumn("jour", to_date(col("datetime")))
         .groupBy("jour", "ville", "polluant")
         .agg(
             avg("valeur").alias("moy"),
             smax("valeur").alias("pic"),
             count("*").alias("n_obs")
         ))

print("Nb lignes agrégées :", out.count())
out.show(10, truncate=False)

# Écriture en table Postgres
(out.write
    .format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", "prod.aggr_ville_jour_polluant")
    .option("user", "yasminedri")
    .option("password", "qualair")
    .option("driver", "org.postgresql.Driver")
    .mode("overwrite")
    .save())

spark.stop()
