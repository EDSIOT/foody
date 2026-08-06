import time
import random
import logging
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

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


def chunk_with_anchor(d, anchor_name, size=5):
    others = {k: v for k, v in d.items() if k != anchor_name}
    items = list(others.items())
    slots_per_batch = size - 1
    for i in range(0, len(items), slots_per_batch):
        batch = dict(items[i:i + slots_per_batch])
        batch[anchor_name] = d[anchor_name]
        yield batch


def fetch_batch(batch, geo='FR', timeframe='now 7-d', retries=4):
    mids = list(batch.values())
    mid_to_name = {v: k for k, v in batch.items()}
    batch_names = list(batch.keys())

    for attempt in range(retries):
        try:
            pytrends = TrendReq(hl='fr-FR', tz=60)
            pytrends.build_payload(kw_list=mids, timeframe=timeframe, geo=geo)
            df = pytrends.interest_by_region(
                resolution='CITY', inc_low_vol=True, inc_geo_code=True
            )
            df = df.rename(columns=mid_to_name)
            logger.info(f"Lot réussi: {batch_names} ({len(df)} villes)")
            return df
        except Exception as e:
            wait = (2 ** attempt) * 30 + random.uniform(0, 10)
            logger.warning(
                f"Échec tentative {attempt + 1}/{retries} pour {batch_names}: {e} "
                f"— pause {wait:.0f}s"
            )
            time.sleep(wait)

    logger.error(f"Échec définitif pour le lot: {batch_names}")
    return None


def fetch_all_cuisines(geo='FR', timeframe='now 7-d', pause_between_batches=(20, 40)):
    """Récupère tous les lots, renvoie une liste de DataFrames bruts (non normalisés)."""
    results = []
    failed_batches = []

    batches = list(chunk_with_anchor(CUISINE_TOPICS, ANCHOR_NAME, size=5))
    logger.info(f"Démarrage ingestion — {len(batches)} lots à traiter")

    for i, batch in enumerate(batches, 1):
        logger.info(f"Lot {i}/{len(batches)}: {list(batch.keys())}")
        df = fetch_batch(batch, geo=geo, timeframe=timeframe)
        if df is not None:
            results.append(df)
        else:
            failed_batches.append(list(batch.keys()))

        if i < len(batches):
            pause = random.uniform(*pause_between_batches)
            time.sleep(pause)

    if failed_batches:
        logger.warning(f"{len(failed_batches)} lot(s) échoué(s): {failed_batches}")

    logger.info(f"Ingestion terminée — {len(results)}/{len(batches)} lots réussis")
    return results, failed_batches


def normalize_batches(batches_data, anchor_name=ANCHOR_NAME):
    """Normalise tous les lots par rapport au premier, via l'ancre commune."""
    if not batches_data:
        return None

    df_ref = batches_data[0]
    pizza_ref = df_ref[anchor_name].mean()
    normalized_dfs = [df_ref]

    for df_batch in batches_data[1:]:
        pizza_batch = df_batch[anchor_name].mean()
        if pizza_batch == 0:
            logger.warning("Ancre à 0 dans un lot — normalisation impossible, lot ignoré")
            continue
        facteur = pizza_ref / pizza_batch
        cols_to_scale = [c for c in df_batch.columns if c not in ['geoCode', anchor_name]]
        df_scaled = df_batch.copy()
        df_scaled[cols_to_scale] = df_scaled[cols_to_scale] * facteur
        normalized_dfs.append(df_scaled.drop(columns=[anchor_name]))

    df_final = normalized_dfs[0]
    for df_next in normalized_dfs[1:]:
        cols_to_merge = [c for c in df_next.columns if c != 'geoCode']
        df_final = df_final.join(df_next[cols_to_merge], how='outer')

    logger.info(f"Normalisation terminée — {df_final.shape[1] - 1} cuisines, {len(df_final)} villes")
    return df_final