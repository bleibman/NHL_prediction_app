"""Stanley Cup prediction model.

Uses historical season stats and playoff outcomes to predict series winners
and simulate a full playoff bracket to estimate Stanley Cup probabilities.
"""

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from db.supabase import select

logger = logging.getLogger(__name__)

_FEATURE_COLS = [
    "points_pct",
    "gf_ga_ratio",
    "pp_pct",
    "pk_pct",
    "shots_for_pg",
    "shots_against_pg",
    "faceoff_pct",
]


def _load_season_stats() -> pd.DataFrame:
    """Load season stats for all teams/seasons into a DataFrame."""
    rows = select(
        "season_stats",
        columns="season_id,team_id,games_played,wins,losses,ot_losses,points,"
                "point_pct,goals_for,goals_against,pp_pct,pk_pct,"
                "shots_for_pg,shots_against_pg,faceoff_pct",
        filters={"games_played": "gt.0"},
    )
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Join team info
    teams = select("teams", columns="id,abbreviation,name")
    teams_df = pd.DataFrame(teams).rename(columns={"id": "team_id", "name": "team_name"})
    df = df.merge(teams_df, on="team_id", how="left")

    # Derived features
    df["points_pct"] = df["point_pct"].fillna(
        df["points"] / (df["games_played"] * 2)
    )
    df["gf_ga_ratio"] = df["goals_for"] / df["goals_against"].replace(0, 1)

    return df


def _load_playoff_series() -> pd.DataFrame:
    """Load historical playoff series with winners."""
    rows = select(
        "playoff_series",
        columns="season_id,round,top_seed_id,bottom_seed_id,"
                "top_seed_wins,bottom_seed_wins,winning_team_id",
        filters={"winning_team_id": "not.is.null"},
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _build_training_data(
    stats: pd.DataFrame, series: pd.DataFrame
) -> tuple[pd.DataFrame, pd.Series]:
    """Build feature matrix and labels from historical data.

    For each series, create a row with the stat difference between
    top_seed and bottom_seed.  Label = 1 if top_seed won.
    """
    rows = []
    for _, s in series.iterrows():
        t1 = stats[
            (stats["season_id"] == s["season_id"])
            & (stats["team_id"] == s["top_seed_id"])
        ]
        t2 = stats[
            (stats["season_id"] == s["season_id"])
            & (stats["team_id"] == s["bottom_seed_id"])
        ]
        if t1.empty or t2.empty:
            continue

        t1, t2 = t1.iloc[0], t2.iloc[0]
        row = {}
        for col in _FEATURE_COLS:
            v1 = t1.get(col, 0) or 0
            v2 = t2.get(col, 0) or 0
            row[f"diff_{col}"] = float(v1) - float(v2)

        row["label"] = 1 if s["winning_team_id"] == s["top_seed_id"] else 0
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=int)
    X = df[[f"diff_{c}" for c in _FEATURE_COLS]]
    y = df["label"]
    return X, y


class StanleyCupPredictor:
    """Train on historical playoff series and predict current-season outcomes."""

    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.1, random_state=42,
        )
        self._stats: pd.DataFrame = pd.DataFrame()
        self._trained = False

    def train(self):
        logger.info("Loading data for training")
        self._stats = _load_season_stats()
        series = _load_playoff_series()

        if series.empty:
            logger.warning("No playoff series data — cannot train")
            return

        X, y = _build_training_data(self._stats, series)
        if X.empty:
            logger.warning("No valid training samples")
            return

        self.model.fit(X, y)
        self._trained = True
        logger.info("Trained on %d series matchups", len(X))

    def predict_series(self, team1_id: int, team2_id: int, season_id: int) -> float:
        """Return probability that team1 wins a series vs team2."""
        if not self._trained:
            return 0.5

        t1 = self._stats[
            (self._stats["season_id"] == season_id) & (self._stats["team_id"] == team1_id)
        ]
        t2 = self._stats[
            (self._stats["season_id"] == season_id) & (self._stats["team_id"] == team2_id)
        ]
        if t1.empty or t2.empty:
            return 0.5

        t1, t2 = t1.iloc[0], t2.iloc[0]
        features = {}
        for col in _FEATURE_COLS:
            v1 = t1.get(col, 0) or 0
            v2 = t2.get(col, 0) or 0
            features[f"diff_{col}"] = float(v1) - float(v2)

        X = pd.DataFrame([features])
        prob = self.model.predict_proba(X)[0]
        return float(prob[1])

    def simulate_bracket(
        self, matchups: list[tuple[int, int]], season_id: int, n_simulations: int = 5000
    ) -> dict[int, float]:
        """Simulate a full playoff bracket and return Cup-win probabilities."""
        win_counts: dict[int, int] = {}

        for _ in range(n_simulations):
            current = list(matchups)
            champion = None
            for _round in range(10):  # enough rounds for any bracket size
                winners = []
                for t1, t2 in current:
                    p = self.predict_series(t1, t2, season_id)
                    winners.append(t1 if np.random.random() < p else t2)

                if len(winners) == 1:
                    champion = winners[0]
                    break

                # Pair winners for next round; odd team gets a bye
                current = []
                for i in range(0, len(winners) - 1, 2):
                    current.append((winners[i], winners[i + 1]))
                if len(winners) % 2 == 1:
                    current.append((winners[-1], winners[-1]))

                if not current:
                    break

            if champion is None:
                continue

            win_counts[champion] = win_counts.get(champion, 0) + 1

        total = sum(win_counts.values()) or 1
        return {
            tid: count / total
            for tid, count in sorted(win_counts.items(), key=lambda x: -x[1])
        }

    def get_current_predictions(self, season_id: int | None = None) -> pd.DataFrame:
        """Return per-team Cup-win probabilities for the given (or latest) season."""
        if self._stats.empty:
            self._stats = _load_season_stats()
        if self._stats.empty:
            return pd.DataFrame()

        if season_id is None:
            season_id = int(self._stats["season_id"].max())

        # Try to use actual R1 matchups from DB
        r1 = select(
            "playoff_series",
            columns="top_seed_id,bottom_seed_id",
            filters={"season_id": f"eq.{season_id}", "round": "eq.1"},
        )

        if r1 and len(r1) == 8:
            matchups = [(s["top_seed_id"], s["bottom_seed_id"]) for s in r1]
        else:
            # Seed top 16 by points
            cur = self._stats[self._stats["season_id"] == season_id].nlargest(16, "points")
            if len(cur) < 16:
                logger.warning("Not enough teams for bracket in season %d", season_id)
                return pd.DataFrame()
            ids = cur["team_id"].tolist()
            matchups = [(ids[i], ids[15 - i]) for i in range(8)]

        probs = self.simulate_bracket(matchups, season_id)

        rows = []
        for tid, prob in probs.items():
            team_row = self._stats[self._stats["team_id"] == tid]
            if not team_row.empty:
                tr = team_row.iloc[0]
                rows.append({
                    "team_id": tid,
                    "abbreviation": tr.get("abbreviation", "???"),
                    "team_name": tr.get("team_name", "Unknown"),
                    "cup_probability": round(prob * 100, 2),
                })
            else:
                rows.append({
                    "team_id": tid,
                    "abbreviation": "???",
                    "team_name": "Unknown",
                    "cup_probability": round(prob * 100, 2),
                })

        return pd.DataFrame(rows).sort_values(
            "cup_probability", ascending=False
        ).reset_index(drop=True)
