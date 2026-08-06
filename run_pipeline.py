import logging
import sys
from datetime import datetime
from pathlib import Path

from ingestion.fetch_trends import fetch_all_cuisines, normalize_batches, ANCHOR_NAME
from ingestion.db import get_engine, ensure_schema, insert_cuisine_trends


def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    log_filename = f"logs/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return log_filename


def main():
    log_file = setup_logging()
    logger = logging.getLogger("run_pipeline")

    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("DÉMARRAGE DU PIPELINE FOODY")
    logger.info("=" * 60)

    try:
        # --- 1. Connexion base + schéma ---
        logger.info("Étape 1/4 — Connexion à la base de données")
        engine = get_engine()
        ensure_schema(engine)

        # --- 2. Ingestion Google Trends ---
        logger.info("Étape 2/4 — Ingestion des données Google Trends")
        batches_data, failed_batches = fetch_all_cuisines(geo='FR', timeframe='now 7-d')

        if not batches_data:
            logger.error("Aucune donnée récupérée — arrêt du pipeline")
            sys.exit(1)

        # --- 3. Normalisation ---
        logger.info("Étape 3/4 — Normalisation des scores")
        df_final = normalize_batches(batches_data, anchor_name=ANCHOR_NAME)

        if df_final is None:
            logger.error("Échec de la normalisation — arrêt du pipeline")
            sys.exit(1)

        # --- 4. Insertion en base ---
        logger.info("Étape 4/4 — Insertion en base de données")
        n_inserted = insert_cuisine_trends(engine, df_final, anchor_name=ANCHOR_NAME)

        # --- Résumé final ---
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info("PIPELINE TERMINÉ AVEC SUCCÈS")
        logger.info(f"Durée totale: {duration:.1f}s")
        logger.info(f"Lignes insérées: {n_inserted}")
        if failed_batches:
            logger.warning(f"Lots échoués (données partielles): {failed_batches}")
        logger.info(f"Log complet: {log_file}")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"ERREUR FATALE — arrêt du pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()