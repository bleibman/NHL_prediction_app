"""Streamlit entrypoint for the NHL Stanley Cup Prediction App."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db.supabase import select
from models.predictor import StanleyCupPredictor
from ui.components import (
    format_season,
    highlight_card,
    info_box,
    inject_css,
    page_header,
    section_divider,
    stat_card,
)
from ui.theme import PLOTLY_LAYOUT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="NHL Stanley Cup Predictions",
    page_icon="\U0001F3D2",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_resource
def get_predictor() -> StanleyCupPredictor:
    predictor = StanleyCupPredictor()
    predictor.train()
    return predictor


def query_df(table: str, columns: str = "*", **filters) -> pd.DataFrame:
    rows = select(table, columns=columns, filters=filters if filters else None)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _build_standings_df(rows: list[dict], teams_map: dict[int, str]) -> pd.DataFrame:
    """Transform raw season_stats rows into a display-ready standings DataFrame."""
    for row in rows:
        row["Team"] = teams_map.get(row.pop("team_id"), "?")
        row["PP%"] = round((row.pop("pp_pct") or 0) * 100, 1)
        row["PK%"] = round((row.pop("pk_pct") or 0) * 100, 1)
        row["FO%"] = round((row.pop("faceoff_pct") or 0) * 100, 1)
        row["PTS%"] = round((row.pop("point_pct") or 0) * 100, 1)
        row["SF/G"] = round(row.pop("shots_for_pg") or 0, 1)
        row["SA/G"] = round(row.pop("shots_against_pg") or 0, 1)

    return pd.DataFrame(rows).rename(
        columns={
            "games_played": "GP",
            "wins": "W",
            "losses": "L",
            "ot_losses": "OTL",
            "points": "PTS",
            "goals_for": "GF",
            "goals_against": "GA",
        }
    )


STANDINGS_COLS = [
    "Team", "GP", "W", "L", "OTL", "PTS", "PTS%",
    "GF", "GA", "PP%", "PK%", "FO%", "SF/G", "SA/G",
]


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<h2>\U0001F3D2 NHL Predictions</h2>'
        '<p>Stanley Cup Forecast Engine</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        [
            "\U0001F4CA  Dashboard",
            "\U0001F4DA  Historical Data",
            "\U0001F52E  Predictions",
            "\U0001F504  Data Refresh",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Data source: NHL API")
    st.caption("Seasons: 2005\u201306 through 2024\u201325")


# Strip emoji prefix to get clean page name
page_name = page.split("  ", 1)[-1].strip()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

if page_name == "Dashboard":
    page_header("Dashboard", "Current standings and team performance overview")

    seasons = query_df(
        "season_stats", columns="season_id", order="season_id.desc", limit=1
    )
    if seasons.empty:
        st.warning("No data in the database. Go to **Data Refresh** to seed it.")
        st.stop()

    latest = int(seasons.iloc[0]["season_id"])

    # --- Metrics row ---
    games = select("games", columns="id", filters={"season_id": f"eq.{latest}"})
    playoffs = select(
        "playoff_series", columns="id", filters={"season_id": f"eq.{latest}"}
    )
    players = select(
        "player_stats", columns="id", filters={"season_id": f"eq.{latest}"}
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("Season", format_season(latest))
    with c2:
        stat_card("Games Played", f"{len(games):,}")
    with c3:
        stat_card("Playoff Series", str(len(playoffs)))
    with c4:
        stat_card("Players Tracked", f"{len(players):,}")

    section_divider()

    # --- Standings table ---
    st.subheader("Standings")

    stats = select(
        "season_stats",
        columns="team_id,games_played,wins,losses,ot_losses,points,"
        "goals_for,goals_against,pp_pct,pk_pct,faceoff_pct,"
        "point_pct,shots_for_pg,shots_against_pg",
        filters={"season_id": f"eq.{latest}"},
        order="points.desc",
    )
    teams_map = {t["id"]: t["abbreviation"] for t in select("teams", columns="id,abbreviation")}

    if stats:
        df = _build_standings_df(stats, teams_map)

        st.dataframe(
            df[STANDINGS_COLS],
            width="stretch",
            hide_index=True,
            column_config={
                "Team": st.column_config.TextColumn("Team", width="small"),
                "PTS": st.column_config.NumberColumn("PTS", format="%d"),
                "PTS%": st.column_config.ProgressColumn(
                    "PTS%", min_value=0, max_value=100, format="%.1f%%"
                ),
                "PP%": st.column_config.NumberColumn("PP%", format="%.1f%%"),
                "PK%": st.column_config.NumberColumn("PK%", format="%.1f%%"),
                "FO%": st.column_config.NumberColumn("FO%", format="%.1f%%"),
            },
        )

    section_divider()

    # --- Top scorers preview ---
    st.subheader("Top 10 Scorers")
    top_players = select(
        "player_stats",
        columns="player_name,team_abbrev,position,games_played,goals,assists,points",
        filters={"season_id": f"eq.{latest}"},
        order="points.desc",
        limit=10,
    )
    if top_players:
        pdf = pd.DataFrame(top_players).rename(
            columns={
                "player_name": "Player",
                "team_abbrev": "Team",
                "position": "Pos",
                "games_played": "GP",
                "goals": "G",
                "assists": "A",
                "points": "PTS",
            }
        )
        st.dataframe(pdf, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Historical Data
# ---------------------------------------------------------------------------

elif page_name == "Historical Data":
    page_header("Historical Data", "Browse and compare team performance across seasons")

    all_seasons = select("season_stats", columns="season_id", order="season_id.asc")
    if not all_seasons:
        st.warning("No data available.")
        st.stop()

    season_ids = sorted(set(r["season_id"] for r in all_seasons))

    selected = st.selectbox(
        "Season",
        season_ids,
        index=len(season_ids) - 1,
        format_func=format_season,
    )

    teams_list = select("teams", columns="id,abbreviation")
    tmap = {t["id"]: t["abbreviation"] for t in teams_list}

    tab1, tab2, tab3 = st.tabs([
        "\U0001F4CA  Team Stats",
        "\U0001F3AF  Top Scorers",
        "\U0001F3C6  Playoff Results",
    ])

    # --- Team stats tab ---
    with tab1:
        rows = select(
            "season_stats",
            columns="team_id,games_played,wins,losses,ot_losses,points,point_pct,"
            "goals_for,goals_against,pp_pct,pk_pct,"
            "shots_for_pg,shots_against_pg,faceoff_pct",
            filters={"season_id": f"eq.{selected}"},
            order="points.desc",
        )
        if rows:
            df = _build_standings_df(rows, tmap)

            st.dataframe(
                df[STANDINGS_COLS],
                width="stretch",
                hide_index=True,
                column_config={
                    "PTS%": st.column_config.ProgressColumn(
                        "PTS%", min_value=0, max_value=100, format="%.1f%%"
                    ),
                },
            )
        else:
            st.info("No team stats for this season.")

    # --- Top scorers tab ---
    with tab2:
        players = select(
            "player_stats",
            columns="player_name,team_abbrev,position,games_played,"
            "goals,assists,points,plus_minus",
            filters={"season_id": f"eq.{selected}"},
            order="points.desc",
            limit=50,
        )
        if players:
            df = pd.DataFrame(players).rename(
                columns={
                    "player_name": "Player",
                    "team_abbrev": "Team",
                    "position": "Pos",
                    "games_played": "GP",
                    "goals": "G",
                    "assists": "A",
                    "points": "PTS",
                    "plus_minus": "+/-",
                }
            )
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "+/-": st.column_config.NumberColumn("+/-", format="%+d"),
                },
            )
        else:
            st.info("No player stats for this season.")

    # --- Playoff results tab ---
    with tab3:
        series = select(
            "playoff_series",
            columns="round,top_seed_id,bottom_seed_id,"
            "top_seed_wins,bottom_seed_wins,winning_team_id",
            filters={"season_id": f"eq.{selected}"},
            order="round.asc",
        )
        if series:
            round_names = {1: "Round 1", 2: "Round 2", 3: "Conf. Finals", 4: "Stanley Cup Final"}

            for r in series:
                r["Round"] = round_names.get(r.pop("round"), "?")
                top_abbrev = tmap.get(r.pop("top_seed_id"), "?")
                bot_abbrev = tmap.get(r.pop("bottom_seed_id"), "?")
                winner = tmap.get(r.pop("winning_team_id"), "?")
                tw = r.pop("top_seed_wins")
                bw = r.pop("bottom_seed_wins")
                r["Matchup"] = f"{top_abbrev}  vs  {bot_abbrev}"
                r["Score"] = f"{tw}\u2013{bw}"
                r["Winner"] = winner

            df = pd.DataFrame(series)
            st.dataframe(
                df[["Round", "Matchup", "Score", "Winner"]],
                width="stretch",
                hide_index=True,
                column_config={
                    "Round": st.column_config.TextColumn("Round", width="small"),
                    "Matchup": st.column_config.TextColumn("Matchup", width="medium"),
                },
            )

            # Highlight champion
            final = [s for s in series if s["Round"] == "Stanley Cup Final"]
            if final:
                highlight_card(
                    label="Stanley Cup Champion",
                    icon="\U0001F3C6",
                    title=final[0]["Winner"],
                )
        else:
            st.info("No playoff data for this season.")

    section_divider()

    # --- Cross-season team comparison ---
    st.subheader("Team Trends")
    if teams_list:
        abbrevs = sorted(t["abbreviation"] for t in teams_list)
        team_pick = st.selectbox("Select a team", abbrevs)
        pick_id = next(
            (t["id"] for t in teams_list if t["abbreviation"] == team_pick), None
        )
        if pick_id:
            history = select(
                "season_stats",
                columns="season_id,wins,losses,points,goals_for,goals_against,point_pct",
                filters={"team_id": f"eq.{pick_id}"},
                order="season_id.asc",
            )
            if history:
                hdf = pd.DataFrame(history)
                hdf["Season"] = hdf["season_id"].apply(format_season)
                hdf["PTS%"] = (hdf["point_pct"].fillna(0) * 100).round(1)
                hdf["GF/GA"] = (hdf["goals_for"] / hdf["goals_against"].replace(0, 1)).round(2)

                metric_choice = st.radio(
                    "Metric",
                    ["Points", "PTS%", "Goals For", "Goals Against", "GF/GA Ratio"],
                    horizontal=True,
                )
                col_map = {
                    "Points": "points",
                    "PTS%": "PTS%",
                    "Goals For": "goals_for",
                    "Goals Against": "goals_against",
                    "GF/GA Ratio": "GF/GA",
                }
                y_col = col_map[metric_choice]

                fig = px.line(
                    hdf,
                    x="Season",
                    y=y_col,
                    markers=True,
                    color_discrete_sequence=["#1f6feb"],
                )
                fig.update_layout(
                    **PLOTLY_LAYOUT,
                    yaxis_title=metric_choice,
                    xaxis_title="",
                    showlegend=False,
                    height=350,
                )
                fig.update_traces(
                    line=dict(width=2.5),
                    marker=dict(size=6),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No historical data for {team_pick}.")


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------

elif page_name == "Predictions":
    page_header(
        "Stanley Cup Predictions",
        "ML-powered bracket simulation using historical performance data",
    )

    all_seasons = select("season_stats", columns="season_id", order="season_id.desc")
    if not all_seasons:
        st.warning("No data available. Seed the database first.")
        st.stop()

    season_ids = sorted(set(r["season_id"] for r in all_seasons), reverse=True)

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected = st.selectbox(
            "Predict for season",
            season_ids,
            format_func=format_season,
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("Run Prediction", use_container_width=True)

    if run:
        with st.spinner("Training model and simulating 5,000 brackets..."):
            predictor = get_predictor()
            predictions = predictor.get_current_predictions(season_id=selected)

        if predictions.empty:
            st.error("Not enough data to generate predictions.")
        else:
            section_divider()

            # --- Top contender highlight ---
            top = predictions.iloc[0]
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                highlight_card(
                    label="Predicted Favorite",
                    icon="\U0001F3C6",
                    title=top["team_name"],
                    subtitle=f'{top["abbreviation"]} \u2014 {top["cup_probability"]:.1f}% chance',
                )

            section_divider()

            # --- Bar chart ---
            st.subheader("Win Probabilities")
            chart_df = predictions.head(16).copy()
            chart_df = chart_df.sort_values("cup_probability", ascending=True)

            fig = go.Figure(
                go.Bar(
                    x=chart_df["cup_probability"],
                    y=chart_df["abbreviation"],
                    orientation="h",
                    marker=dict(
                        color=chart_df["cup_probability"],
                        colorscale=[[0, "#21262d"], [0.5, "#1f6feb"], [1, "#58a6ff"]],
                    ),
                    text=chart_df["cup_probability"].apply(lambda v: f"{v:.1f}%"),
                    textposition="outside",
                    textfont=dict(color="#c9d1d9", size=12),
                )
            )
            fig.update_layout(
                **PLOTLY_LAYOUT,
                height=max(400, len(chart_df) * 32),
                xaxis_title="Win Probability (%)",
                yaxis_title="",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Full table ---
            st.subheader("All Teams")
            display = predictions.rename(
                columns={
                    "abbreviation": "Team",
                    "team_name": "Name",
                    "cup_probability": "Win %",
                }
            )[["Team", "Name", "Win %"]]
            display.insert(0, "Rank", range(1, len(display) + 1))

            st.dataframe(
                display,
                width="stretch",
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Team": st.column_config.TextColumn("Team", width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Win %": st.column_config.ProgressColumn(
                        "Win %",
                        min_value=0,
                        max_value=predictions["cup_probability"].max() * 1.1,
                        format="%.1f%%",
                    ),
                },
            )


# ---------------------------------------------------------------------------
# Data Refresh
# ---------------------------------------------------------------------------

elif page_name == "Data Refresh":
    page_header("Data Refresh", "Fetch the latest data from the NHL API")

    info_box(
        "The ETL pipeline fetches teams, season stats, game results, "
        "playoff series, and player stats from the NHL API and upserts them "
        "into the database."
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Refresh All Seasons")
        st.caption("Re-fetches data for all 20 seasons (2005\u201325). Games fetch is slow.")
        refresh_all = st.button("Refresh All", use_container_width=True)

    with c2:
        st.markdown("##### Refresh Single Season")
        single = st.number_input(
            "Season ID",
            min_value=20052006,
            max_value=20252026,
            value=20242025,
            step=10001,
            label_visibility="collapsed",
        )
        st.caption(f"Will refresh {format_season(int(single))} only.")
        refresh_single = st.button("Refresh Season", use_container_width=True)

    if refresh_all or refresh_single:
        season_arg = None if refresh_all else int(single)

        from etl.teams import fetch_and_upsert_teams
        from etl.seasons import fetch_and_upsert_seasons
        from etl.games import fetch_and_upsert_games
        from etl.playoffs import fetch_and_upsert_playoffs
        from etl.player_stats import fetch_and_upsert_player_stats

        steps = [
            ("Teams", "\U0001F3D2", fetch_and_upsert_teams),
            ("Season Stats", "\U0001F4CA", lambda: fetch_and_upsert_seasons(season_arg)),
            ("Games", "\U0001F3AE", lambda: fetch_and_upsert_games(season_arg)),
            ("Playoffs", "\U0001F3C6", lambda: fetch_and_upsert_playoffs(season_arg)),
            ("Player Stats", "\U0001F464", lambda: fetch_and_upsert_player_stats(season_arg)),
        ]

        bar = st.progress(0, text="Starting ETL pipeline...")

        for i, (label, icon, func) in enumerate(steps):
            bar.progress(
                i / len(steps),
                text=f"{icon}  Fetching {label}... ({i + 1}/{len(steps)})",
            )
            try:
                func()
            except Exception as e:
                st.error(f"Error during {label}: {e}")
                logger.exception("ETL error")
                break
            bar.progress((i + 1) / len(steps), text=f"{icon}  {label} complete")

        bar.progress(1.0, text="Pipeline complete")
        st.success("Data refresh complete. Reload the page to see updated data.")
        get_predictor.clear()
