from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_cuisine_trends (
    id SERIAL PRIMARY KEY,
    cuisine_name TEXT NOT NULL,
    city_name TEXT NOT NULL,
    geo_code TEXT,
    interest_score FLOAT NOT NULL,
    is_normalized BOOLEAN DEFAULT FALSE,
    anchor_used TEXT,
    country_code VARCHAR(2) DEFAULT 'FR',
    captured_at TIMESTAMP DEFAULT now()
);
"""

with engine.connect() as conn:
    conn.execute(text(CREATE_TABLE_SQL))
    conn.commit()
    print("✅ Table créée (ou déjà existante)")