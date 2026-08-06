import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# --- 1. Charger le CSV ---
df = pd.read_csv('cuisines_by_city_normalized.csv', index_col=0)
df.index.name = 'city_name'
df = df.reset_index()

print("Colonnes détectées:", df.columns.tolist())
print(df.head())

# --- 2. Passer du format large (une colonne par cuisine) au format long ---
# Colonnes fixes à ne pas "fondre"
id_cols = ['city_name', 'geoCode']
cuisine_cols = [c for c in df.columns if c not in id_cols]

df_long = df.melt(
    id_vars=id_cols,
    value_vars=cuisine_cols,
    var_name='cuisine_name',
    value_name='interest_score'
)

# Retirer les lignes sans donnée (NaN issus des villes absentes de certains lots)
df_long = df_long.dropna(subset=['interest_score'])

# --- 3. Ajouter les métadonnées de traçabilité ---
df_long['geo_code'] = df_long['geoCode']
df_long['country_code'] = 'FR'
df_long['is_normalized'] = True
df_long['anchor_used'] = 'Pizza'  # à adapter si tu as changé d'ancre

df_long = df_long.drop(columns=['geoCode'])

print(f"\n{len(df_long)} lignes prêtes à insérer")
print(df_long.head())

# --- 4. Insertion en base ---
try:
    df_long.to_sql(
        'raw_cuisine_trends',
        engine,
        if_exists='append',
        index=False
    )
    print(f"✅ {len(df_long)} lignes insérées avec succès")
except Exception as e:
    print(f"❌ Erreur d'insertion: {e}")