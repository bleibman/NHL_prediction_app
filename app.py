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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="NHL Stanley Cup Predictions",
    page_icon="\U0001F3D2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* --- Global --- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
}
section[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #c9d1d9 !important;
}

/* --- Typography --- */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #f0f6fc !important;
    font-weight: 700 !important;
}

/* --- Metric cards --- */
[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px 20px;
}
[data-testid="stMetric"] label {
    color: #8b949e !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f0f6fc !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* --- Dataframes --- */
[data-testid="stDataFrame"] {
    border: 1px solid #21262d;
    border-radius: 8px;
    overflow: hidden;
}

/* --- Tabs --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
    color: #8b949e;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: #161b22;
    color: #f0f6fc !important;
    border-bottom: 2px solid #1f6feb;
}

/* --- Buttons --- */
.stButton > button {
    background: #1f6feb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-weight: 600;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #388bfd;
    color: #ffffff;
    border: none;
}

/* --- Sidebar brand --- */
.sidebar-brand {
    text-align: center;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid #21262d;
    margin-bottom: 1rem;
}
.sidebar-brand h2 {
    font-size: 1.3rem !important;
    margin: 0 !important;
    letter-spacing: 0.04em;
}
.sidebar-brand p {
    color: #8b949e;
    font-size: 0.8rem;
    margin: 4px 0 0;
}

/* --- Page header --- */
.page-header {
    padding: 0.5rem 0 1.5rem;
    border-bottom: 1px solid #21262d;
    margin-bottom: 1.5rem;
}
.page-header h1 {
    margin: 0 !important;
    font-size: 1.8rem !important;
}
.page-header p {
    color: #8b949e;
    margin: 4px 0 0;
    font-size: 0.95rem;
}

/* --- Stat card --- */
.stat-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 1rem;
}
.stat-card h4 {
    color: #8b949e !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 6px !important;
    font-weight: 600 !important;
}
.stat-card .value {
    color: #f0f6fc;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
}
.stat-card .sub {
    color: #8b949e;
    font-size: 0.8rem;
    margin-top: 4px;
}

/* --- Divider --- */
.section-divider {
    border: none;
    border-top: 1px solid #21262d;
    margin: 2rem 0;
}

/* --- Footer --- */
.sidebar-footer {
    position: fixed;
    bottom: 0;
    padding: 12px 16px;
    font-size: 0.75rem;
    color: #484f58;
    border-top: 1px solid #21262d;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Plotly theme
# ---------------------------------------------------------------------------
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c9d1d9", family="Inter, system-ui, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
    yaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
)

NHL_COLORS = [
    "#1f6feb", "#388bfd", "#58a6ff", "#79c0ff",
    "#3fb950", "#56d364", "#f0883e", "#d29922",
    "#f85149", "#da3633", "#bc8cff", "#8b949e",
]


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


def format_season(s: int) -> str:
    return f"{s // 10000}\u2013{str(s // 10000 + 1)[-2:]}"


def page_header(title: str, subtitle: str):
    st.markdown(
        f'<div class="page-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def stat_card(label: str, value, sub: str = ""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="stat-card">'
        f'<h4>{label}</h4>'
        f'<div class="value">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


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

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

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
        for row in stats:
            row["Team"] = teams_map.get(row.pop("team_id"), "?")
            row["PP%"] = round((row.pop("pp_pct") or 0) * 100, 1)
            row["PK%"] = round((row.pop("pk_pct") or 0) * 100, 1)
            row["FO%"] = round((row.pop("faceoff_pct") or 0) * 100, 1)
            row["PTS%"] = round((row.pop("point_pct") or 0) * 100, 1)
            row["SF/G"] = round(row.pop("shots_for_pg") or 0, 1)
            row["SA/G"] = round(row.pop("shots_against_pg") or 0, 1)

        df = pd.DataFrame(stats).rename(
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

        display_cols = [
            "Team", "GP", "W", "L", "OTL", "PTS", "PTS%",
            "GF", "GA", "PP%", "PK%", "FO%", "SF/G", "SA/G",
        ]

        st.dataframe(
            df[display_cols],
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

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

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
            for r in rows:
                r["Team"] = tmap.get(r.pop("team_id"), "?")
                r["PTS%"] = round((r.pop("point_pct") or 0) * 100, 1)
                r["PP%"] = round((r.pop("pp_pct") or 0) * 100, 1)
                r["PK%"] = round((r.pop("pk_pct") or 0) * 100, 1)
                r["FO%"] = round((r.pop("faceoff_pct") or 0) * 100, 1)
                r["SF/G"] = round(r.pop("shots_for_pg") or 0, 1)
                r["SA/G"] = round(r.pop("shots_against_pg") or 0, 1)

            df = pd.DataFrame(rows).rename(
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

            st.dataframe(
                df[["Team", "GP", "W", "L", "OTL", "PTS", "PTS%",
                    "GF", "GA", "PP%", "PK%", "FO%", "SF/G", "SA/G"]],
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
                champ = final[0]["Winner"]
                st.markdown(
                    f'<div style="text-align:center; padding:1.5rem; margin-top:1rem; '
                    f'background:#161b22; border:1px solid #21262d; border-radius:10px;">'
                    f'<div style="font-size:0.85rem; color:#8b949e; text-transform:uppercase; '
                    f'letter-spacing:0.05em;">Stanley Cup Champion</div>'
                    f'<div style="font-size:2.5rem; margin-top:0.3rem;">\U0001F3C6</div>'
                    f'<div style="font-size:1.5rem; font-weight:700; color:#f0f6fc; '
                    f'margin-top:0.3rem;">{champ}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No playoff data for this season.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

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
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            # --- Top contender highlight ---
            top = predictions.iloc[0]
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown(
                    f'<div style="text-align:center; padding:2rem; '
                    f'background:linear-gradient(135deg, #161b22 0%, #1c2333 100%); '
                    f'border:1px solid #1f6feb; border-radius:12px;">'
                    f'<div style="font-size:0.85rem; color:#8b949e; text-transform:uppercase; '
                    f'letter-spacing:0.05em;">Predicted Favorite</div>'
                    f'<div style="font-size:2rem; margin-top:0.5rem;">\U0001F3C6</div>'
                    f'<div style="font-size:1.8rem; font-weight:700; color:#f0f6fc; '
                    f'margin-top:0.3rem;">{top["team_name"]}</div>'
                    f'<div style="font-size:1rem; color:#1f6feb; margin-top:0.3rem;">'
                    f'{top["abbreviation"]} \u2014 {top["cup_probability"]:.1f}% chance</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

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

    st.markdown(
        '<div style="background:#161b22; border:1px solid #21262d; '
        'border-radius:10px; padding:1.2rem; margin-bottom:1.5rem;">'
        '<p style="color:#c9d1d9; margin:0;">'
        'The ETL pipeline fetches teams, season stats, game results, '
        'playoff series, and player stats from the NHL API and upserts them '
        'into the database.</p></div>',
        unsafe_allow_html=True,
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
