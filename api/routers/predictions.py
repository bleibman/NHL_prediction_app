"""Predictions API endpoints."""

from fastapi import APIRouter

from db.supabase import select
from models.predictor import StanleyCupPredictor
from api.schemas import PredictionRequest, PredictionRow

router = APIRouter()


def _format_season(s: int) -> str:
    return f"{s // 10000}\u2013{str(s // 10000 + 1)[-2:]}"


@router.get("/seasons", response_model=list[int])
def get_seasons():
    rows = select("season_stats", columns="season_id", order="season_id.desc")
    if not rows:
        return []
    return sorted(set(r["season_id"] for r in rows), reverse=True)


@router.post("/run", response_model=list[PredictionRow])
def run_predictions(body: PredictionRequest):
    predictor = StanleyCupPredictor()
    predictor.train()
    df = predictor.get_current_predictions(season_id=body.season_id)

    if df.empty:
        return []

    result = []
    for i, (_, row) in enumerate(df.iterrows()):
        result.append(PredictionRow(
            rank=i + 1,
            team_id=int(row["team_id"]),
            abbreviation=row["abbreviation"],
            team_name=row["team_name"],
            cup_probability=float(row["cup_probability"]),
        ))
    return result
