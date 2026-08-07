from fastapi import APIRouter, Query
from sqlalchemy import text
from ingestion.db import get_engine

router = APIRouter()
engine = get_engine()

@router.get("/cuisines")
def get_cuisines(
    city: str | None = Query(None, description="Filtrer par ville"),
    cuisine: str | None = Query(None, description="Filtrer par type de cuisine"),
    days: int = Query(7, description="Nombre de jours d'historique")
):
    query = """
        SELECT cuisine_name, city_name, interest_score, captured_at
        FROM raw_cuisine_trends
        WHERE captured_at >= now() - (:days || ' days')::interval
    """
    params = {"days": days}

    if city:
        query += " AND city_name = :city"
        params["city"] = city
    if cuisine:
        query += " AND cuisine_name = :cuisine"
        params["cuisine"] = cuisine

    query += " ORDER BY captured_at DESC"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = [dict(row._mapping) for row in result]

    return rows


@router.get("/cuisines/top")
def get_top_cuisine_per_city(days: int = Query(7)):
    """Retourne la cuisine dominante par ville — utile pour la carte."""
    query = """
        SELECT DISTINCT ON (city_name)
            city_name, cuisine_name, interest_score, captured_at
        FROM raw_cuisine_trends
        WHERE captured_at >= now() - (:days || ' days')::interval
        ORDER BY city_name, interest_score DESC, captured_at DESC
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"days": days})
        rows = [dict(row._mapping) for row in result]
    return rows


@router.get("/cities")
def get_cities():
    query = "SELECT DISTINCT city_name FROM raw_cuisine_trends ORDER BY city_name"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [row[0] for row in result]