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
            "\U0001F3AB  Ticket Analytics",
            "\U0001F504  Data Refresh",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Data sources: NHL API, SeatGeek")
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
# Ticket Analytics
# ---------------------------------------------------------------------------

elif page_name == "Ticket Analytics":
    page_header("Ticket Analytics", "NHL ticket prices, trends, and attendance data")

    # Load ticket snapshot data
    snapshots = select(
        "ticket_snapshots",
        columns="seatgeek_event_id,game_date,home_team_id,away_team_id,"
        "snapshot_date,lowest_price,average_price,highest_price,listing_count",
        order="game_date.asc",
    )
    teams_list = select("teams", columns="id,name,abbreviation")
    teams_map = {t["id"]: t["abbreviation"] for t in teams_list}
    teams_name_map = {t["id"]: t["name"] for t in teams_list}

    if not snapshots:
        info_box(
            "No ticket data available yet. Set SEATGEEK_CLIENT_ID in your "
            "environment and run Data Refresh to fetch ticket prices."
        )
    else:
        snap_df = pd.DataFrame(snapshots)

        # --- 1. Price overview cards ---
        latest_date = snap_df["snapshot_date"].max()
        latest = snap_df[snap_df["snapshot_date"] == latest_date]

        avg_ticket = latest["average_price"].mean()
        lowest_avail = latest["lowest_price"].min()
        total_listings = latest["listing_count"].sum()
        games_tracked = len(latest)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            stat_card("Avg Ticket Price", f"${avg_ticket:.0f}" if pd.notna(avg_ticket) else "N/A")
        with c2:
            stat_card("Lowest Available", f"${lowest_avail:.0f}" if pd.notna(lowest_avail) else "N/A")
        with c3:
            stat_card("Total Listings", f"{int(total_listings):,}" if pd.notna(total_listings) else "N/A")
        with c4:
            stat_card("Games Tracked", str(games_tracked), sub=f"as of {latest_date}")

        section_divider()

        # --- 2. Upcoming games table ---
        st.subheader("Upcoming Games")
        upcoming = latest.copy()
        upcoming["Home"] = upcoming["home_team_id"].map(teams_map)
        upcoming["Away"] = upcoming["away_team_id"].map(teams_map)
        upcoming["Date"] = pd.to_datetime(upcoming["game_date"]).dt.strftime("%b %d, %Y")
        upcoming = upcoming.rename(columns={
            "average_price": "Avg $",
            "lowest_price": "Low $",
            "highest_price": "High $",
            "listing_count": "Listings",
        })

        display_cols = ["Date", "Home", "Away", "Avg $", "Low $", "High $", "Listings"]
        available_cols = [c for c in display_cols if c in upcoming.columns]
        st.dataframe(
            upcoming[available_cols].sort_values("Date" if "Date" in available_cols else available_cols[0]),
            width="stretch",
            hide_index=True,
            column_config={
                "Avg $": st.column_config.NumberColumn("Avg $", format="$%d"),
                "Low $": st.column_config.NumberColumn("Low $", format="$%d"),
                "High $": st.column_config.NumberColumn("High $", format="$%d"),
            },
        )

        section_divider()

        # --- 3. Price trends chart ---
        st.subheader("Price Trends")
        unique_dates = snap_df["snapshot_date"].nunique()
        if unique_dates >= 2:
            # Calculate days until game for each snapshot
            trend_df = snap_df.copy()
            trend_df["game_date"] = pd.to_datetime(trend_df["game_date"])
            trend_df["snapshot_date"] = pd.to_datetime(trend_df["snapshot_date"])
            trend_df["days_until_game"] = (
                trend_df["game_date"] - trend_df["snapshot_date"]
            ).dt.days
            trend_df = trend_df[trend_df["days_until_game"] >= 0]

            if not trend_df.empty:
                avg_by_days = (
                    trend_df.groupby("days_until_game")["average_price"]
                    .mean()
                    .reset_index()
                    .sort_values("days_until_game")
                )

                fig = px.line(
                    avg_by_days,
                    x="days_until_game",
                    y="average_price",
                    markers=True,
                    color_discrete_sequence=["#1f6feb"],
                )
                fig.update_layout(
                    **PLOTLY_LAYOUT,
                    xaxis_title="Days Until Game",
                    yaxis_title="Average Price ($)",
                    showlegend=False,
                    height=350,
                )
                fig.update_xaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                info_box("Not enough data points to show price trends yet.")
        else:
            info_box(
                "Price trend analysis requires at least 2 days of snapshot data. "
                "Run the daily ticket fetch to accumulate history."
            )

        section_divider()

        # --- 4. Team price comparison ---
        st.subheader("Average Price by Team")
        team_prices = (
            latest.groupby("home_team_id")["average_price"]
            .mean()
            .reset_index()
            .sort_values("average_price", ascending=True)
        )
        team_prices["team"] = team_prices["home_team_id"].map(teams_map)
        team_prices = team_prices.dropna(subset=["team", "average_price"])

        if not team_prices.empty:
            fig = go.Figure(
                go.Bar(
                    x=team_prices["average_price"],
                    y=team_prices["team"],
                    orientation="h",
                    marker=dict(
                        color=team_prices["average_price"],
                        colorscale=[[0, "#21262d"], [0.5, "#1f6feb"], [1, "#58a6ff"]],
                    ),
                    text=team_prices["average_price"].apply(lambda v: f"${v:.0f}"),
                    textposition="outside",
                    textfont=dict(color="#c9d1d9", size=12),
                )
            )
            fig.update_layout(
                **PLOTLY_LAYOUT,
                height=max(400, len(team_prices) * 28),
                xaxis_title="Average Ticket Price ($)",
                yaxis_title="",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    section_divider()

    # --- 5. Historical attendance ---
    st.subheader("Historical Attendance")
    attendance_games = select(
        "games",
        columns="home_team_id,season_id,attendance",
        filters={"attendance": "not.is.null"},
    )

    if attendance_games:
        att_df = pd.DataFrame(attendance_games)
        att_df["team"] = att_df["home_team_id"].map(teams_map)

        team_options = sorted(att_df["team"].dropna().unique().tolist())
        if team_options:
            selected_team = st.selectbox("Select a team", team_options, key="att_team")
            team_att = att_df[att_df["team"] == selected_team]

            if not team_att.empty:
                season_avg = (
                    team_att.groupby("season_id")["attendance"]
                    .mean()
                    .reset_index()
                    .sort_values("season_id")
                )
                season_avg["Season"] = season_avg["season_id"].apply(format_season)

                fig = px.bar(
                    season_avg,
                    x="Season",
                    y="attendance",
                    color_discrete_sequence=["#1f6feb"],
                )
                fig.update_layout(
                    **PLOTLY_LAYOUT,
                    xaxis_title="",
                    yaxis_title="Average Attendance",
                    showlegend=False,
                    height=350,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                info_box(f"No attendance data for {selected_team}.")
    else:
        info_box(
            "No attendance data imported yet. Download the Kaggle NHL Games CSV "
            "and run: python scripts/import_attendance.py data/nhl_games.csv"
        )

    section_divider()

    # --- 6. Price forecast placeholder ---
    st.subheader("Price Forecast")
    info_box(
        "The price forecasting model requires at least 14 days of accumulated "
        "snapshot data to train. Continue running the daily ticket fetch and "
        "this section will activate automatically once sufficient data is available."
    )


# ---------------------------------------------------------------------------
# Data Refresh
# ---------------------------------------------------------------------------

elif page_name == "Data Refresh":
    page_header("Data Refresh", "Fetch the latest data from the NHL API and SeatGeek")

    info_box(
        "The ETL pipeline fetches teams, season stats, game results, "
        "playoff series, and player stats from the NHL API, plus ticket "
        "prices from SeatGeek, and upserts them into the database."
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
        from etl.seatgeek import fetch_and_upsert_ticket_snapshots

        steps = [
            ("Teams", "\U0001F3D2", fetch_and_upsert_teams),
            ("Season Stats", "\U0001F4CA", lambda: fetch_and_upsert_seasons(season_arg)),
            ("Games", "\U0001F3AE", lambda: fetch_and_upsert_games(season_arg)),
            ("Playoffs", "\U0001F3C6", lambda: fetch_and_upsert_playoffs(season_arg)),
            ("Player Stats", "\U0001F464", lambda: fetch_and_upsert_player_stats(season_arg)),
            ("Ticket Prices", "\U0001F3AB", fetch_and_upsert_ticket_snapshots),
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
