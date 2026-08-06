import time
import logging
import pandas as pd
from pytrends.request import TrendReq

logging.basicConfig(level=logging.INFO)
pytrends = TrendReq(hl='fr-FR', tz=60)

CUISINE_TOPICS = {
    'Pizza': '/m/0663v', 
    'Sushi': '/m/07030',
    'Kebab': '/m/022n8y',
    'Hamburger': '/m/0cdn1',
    'Taco': '/m/07crc',
    'Tacos français': '/g/11c6mbf6r2',
    'Restaurant gastronomique': '/g/121hfhdj',
    'restaurant chinois': '/m/0gx1rv4',
    'restaurant végétarien': '/g/11c5zrnmpz',
    'restaurant italien': '/g/11b6hhzwhm',
    'restaurant mexicain': '/g/11b6hffq31',
    'restaurant indien': '/g/11c2nk3hfl',
    'bar': '/m/01nz0z',
    'bistro': '/m/072qlz',
    'brasserie': '/m/025rvlt',
    'café': '/m/020fb2',
    'crêperie': '/g/1218fg9b',
    'pâtisserie': '/m/0hnyx',
    'traiteur': '/m/02yn76',
    'restaurant asiatique': '/g/11c5zt2ygg',
    'restaurant africain': '/g/11c5yss5mh',
    'restaurant américain': '/g/11c5xwqpht',
    'barbecue': '/g/1223qdcp',
}

ANCHOR_NAME = 'Pizza'
ANCHOR_MID = CUISINE_TOPICS[ANCHOR_NAME]

def chunk_with_anchor(d, anchor_name, size=5):
    """Découpe en lots de `size`, chaque lot incluant systématiquement l'ancre."""
    others = {k: v for k, v in d.items() if k != anchor_name}
    items = list(others.items())
    slots_per_batch = size - 1  # une place réservée à l'ancre
    for i in range(0, len(items), slots_per_batch):
        batch = dict(items[i:i + slots_per_batch])
        batch[anchor_name] = d[anchor_name]
        yield batch

def fetch_batch(batch, geo='FR', timeframe='now 7-d', retries=3):
    mids = list(batch.values())
    mid_to_name = {v: k for k, v in batch.items()}
    for attempt in range(retries):
        try:
            pytrends.build_payload(kw_list=mids, timeframe=timeframe, geo=geo)
            df = pytrends.interest_by_region(resolution='CITY', inc_low_vol=True, inc_geo_code=True)
            df = df.rename(columns=mid_to_name)
            return df
        except Exception as e:
            logging.warning(f"Tentative {attempt+1}/{retries} échouée: {e}")
            time.sleep(30)
    logging.error(f"Échec définitif pour {list(batch.keys())}")
    return None

# --- Récupération de tous les lots ---
batches_data = []
for batch in chunk_with_anchor(CUISINE_TOPICS, ANCHOR_NAME, size=5):
    logging.info(f"Lot: {list(batch.keys())}")
    df = fetch_batch(batch)
    if df is not None:
        batches_data.append(df)
    time.sleep(30)

# --- Normalisation par rapport au premier lot (référence) ---
if batches_data:
    df_ref = batches_data[0]
    pizza_ref = df_ref[ANCHOR_NAME].mean()  # moyenne sur toutes les villes comme point d'ancrage stable

    normalized_dfs = [df_ref]

    for df_batch in batches_data[1:]:
        pizza_batch = df_batch[ANCHOR_NAME].mean()
        if pizza_batch == 0:
            logging.warning("Ancre à 0 dans ce lot, normalisation impossible pour ce lot — ignoré")
            continue
        facteur = pizza_ref / pizza_batch
        cols_to_scale = [c for c in df_batch.columns if c not in ['geoCode', ANCHOR_NAME]]
        df_scaled = df_batch.copy()
        df_scaled[cols_to_scale] = df_scaled[cols_to_scale] * facteur
        normalized_dfs.append(df_scaled.drop(columns=[ANCHOR_NAME]))

    # Fusion finale
    df_final = normalized_dfs[0]
    for df_next in normalized_dfs[1:]:
        cols_to_merge = [c for c in df_next.columns if c != 'geoCode']
        df_final = df_final.join(df_next[cols_to_merge], how='outer')

    print(df_final.round(1))
    df_final.to_csv('cuisines_by_city_normalized.csv')