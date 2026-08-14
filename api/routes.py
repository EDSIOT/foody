from fastapi import APIRouter, Query
from sqlalchemy import text
from ingestion.db import get_engine

router = APIRouter()
engine = get_engine()

@router.get("/cuisines")
def get_cuisines(
    region: str | None = Query(None, description="Filtrer par ville"),
    cuisine: str | None = Query(None, description="Filtrer par type de cuisine"),
    days: int = Query(7, description="Nombre de jours d'historique")
):
    query = """
        SELECT cuisine_name, region_name, interest_score, captured_at
        FROM raw_cuisine_trends
        WHERE captured_at >= now() - (:days || ' days')::interval
    """
    params = {"days": days}

    if region:
        query += " AND region_name = :region"
        params["region"] = region
    if cuisine:
        query += " AND cuisine_name = :cuisine"
        params["cuisine"] = cuisine

    query += " ORDER BY captured_at DESC"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = [dict(row._mapping) for row in result]

    return rows


@router.get("/cuisines/top")
def get_top_cuisine_per_region(days: int = Query(7)):
    """Retourne la cuisine dominante par ville — utile pour la carte."""
    query = """
        SELECT DISTINCT ON (region_name)
            region_name, cuisine_name, interest_score, captured_at
        FROM raw_cuisine_trends
        WHERE captured_at >= now() - (:days || ' days')::interval
        ORDER BY region_name, interest_score DESC, captured_at DESC
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"days": days})
        rows = [dict(row._mapping) for row in result]
    return rows


@router.get("/cities")
def get_cities():
    query = "SELECT DISTINCT region_name FROM raw_cuisine_trends ORDER BY region_name"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [row[0] for row in result]
    
@router.get("/regions/top3")
def get_top3_per_region(days: int = Query(7)):
    """Retourne les 3 cuisines les plus populaires pour chaque région."""
    query = """
        WITH ranked AS (
            SELECT
                region_name,
                cuisine_name,
                interest_score,
                captured_at,
                ROW_NUMBER() OVER (
                    PARTITION BY region_name, cuisine_name
                    ORDER BY captured_at DESC
                ) AS rn
            FROM raw_cuisine_trends
            WHERE captured_at >= now() - (:days || ' days')::interval
        ),
        latest AS (
            SELECT region_name, cuisine_name, interest_score
            FROM ranked WHERE rn = 1
        ),
        top3 AS (
            SELECT
                region_name,
                cuisine_name,
                interest_score,
                ROW_NUMBER() OVER (
                    PARTITION BY region_name
                    ORDER BY interest_score DESC
                ) AS rank
            FROM latest
        )
        SELECT region_name, cuisine_name, interest_score, rank
        FROM top3
        WHERE rank <= 3
        ORDER BY region_name, rank
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"days": days})
        rows = [dict(row._mapping) for row in result]

    # Regrouper par région pour faciliter l'usage côté frontend
    grouped = {}
    for row in rows:
        region = row["region_name"]
        grouped.setdefault(region, []).append({
            "cuisine_name": row["cuisine_name"],
            "interest_score": row["interest_score"],
            "rank": row["rank"]
        })

    return grouped    

@router.get("/cuisines/list")
def get_cuisines_list():
    """Liste des cuisines disponibles, pour peupler le menu déroulant."""
    query = "SELECT DISTINCT cuisine_name FROM raw_cuisine_trends ORDER BY cuisine_name"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [row[0] for row in result]


@router.get("/regions/by-cuisine")
def get_region_scores_for_cuisine(cuisine: str = Query(...), days: int = Query(7)):
    """Score le plus récent d'une cuisine donnée, pour chaque région."""
    query = """
        SELECT DISTINCT ON (region_name)
            region_name, interest_score, captured_at
        FROM raw_cuisine_trends
        WHERE cuisine_name = :cuisine
          AND captured_at >= now() - (:days || ' days')::interval
        ORDER BY region_name, captured_at DESC
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"cuisine": cuisine, "days": days})
        rows = [dict(row._mapping) for row in result]

    return {row["region_name"]: row["interest_score"] for row in rows}