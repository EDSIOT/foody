import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL manquante dans les variables d'environnement")
    return create_engine(database_url)


def ensure_schema(engine):
    create_sql = """
    CREATE TABLE IF NOT EXISTS raw_cuisine_trends (
        id SERIAL PRIMARY KEY,
        cuisine_name TEXT NOT NULL,
        region_name TEXT NOT NULL,
        geo_code TEXT,
        interest_score FLOAT NOT NULL,
        is_normalized BOOLEAN DEFAULT FALSE,
        anchor_used TEXT,
        country_code VARCHAR(2) DEFAULT 'FR',
        captured_at TIMESTAMP DEFAULT now()
    );
    """
    with engine.connect() as conn:
        conn.execute(text(create_sql))
        conn.commit()
    logger.info("Schéma vérifié/créé")


def insert_cuisine_trends(engine, df_wide, anchor_name, country_code='FR'):
    df = df_wide.reset_index()
    df.index.name = None
    df = df.rename(columns={df.columns[0]: 'region_name'})

    id_cols = ['region_name', 'geoCode']
    cuisine_cols = [c for c in df.columns if c not in id_cols]

    df_long = df.melt(
        id_vars=id_cols,
        value_vars=cuisine_cols,
        var_name='cuisine_name',
        value_name='interest_score'
    )
    df_long = df_long.dropna(subset=['interest_score'])
    df_long['geo_code'] = df_long['geoCode']
    df_long['country_code'] = country_code
    df_long['is_normalized'] = True
    df_long['anchor_used'] = anchor_name
    df_long = df_long.drop(columns=['geoCode'])

    df_long.to_sql('raw_cuisine_trends', engine, if_exists='append', index=False)
    logger.info(f"{len(df_long)} lignes insérées en base")
    return len(df_long)