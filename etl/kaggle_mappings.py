"""Shared team name / ID resolution for Kaggle dataset imports.

Three incompatible ID systems:
  1. flynn28: full team names  → NHL API team IDs
  2. coletti: ESPN team IDs    → NHL API team IDs
  3. mexwell: MoneyPuck abbrevs → standard NHL abbreviations
"""

# ---------------------------------------------------------------------------
# flynn28 + coletti: team name → NHL API team ID
# Covers current teams + historical names that appear in the CSVs.
# ---------------------------------------------------------------------------
TEAM_NAME_TO_ID: dict[str, int] = {
    # Current teams (2024-25)
    "Anaheim Ducks": 24,
    "Arizona Coyotes": 53,
    "Boston Bruins": 6,
    "Buffalo Sabres": 7,
    "Calgary Flames": 20,
    "Carolina Hurricanes": 12,
    "Chicago Blackhawks": 16,
    "Colorado Avalanche": 21,
    "Columbus Blue Jackets": 29,
    "Dallas Stars": 25,
    "Detroit Red Wings": 17,
    "Edmonton Oilers": 22,
    "Florida Panthers": 13,
    "Los Angeles Kings": 26,
    "Minnesota Wild": 30,
    "Canadiens de Montréal": 8,
    "Montreal Canadiens": 8,
    "Montréal Canadiens": 8,
    "Nashville Predators": 18,
    "New Jersey Devils": 1,
    "New York Islanders": 2,
    "New York Rangers": 3,
    "Ottawa Senators": 9,
    "Philadelphia Flyers": 4,
    "Pittsburgh Penguins": 5,
    "San Jose Sharks": 28,
    "Seattle Kraken": 55,
    "St. Louis Blues": 19,
    "St Louis Blues": 19,
    "Tampa Bay Lightning": 14,
    "Toronto Maple Leafs": 10,
    "Utah Hockey Club": 59,
    "Vancouver Canucks": 23,
    "Vegas Golden Knights": 54,
    "Washington Capitals": 15,
    "Winnipeg Jets": 52,
    # Historical names (flynn28 pre-2005 data we skip, but included for completeness)
    "Mighty Ducks of Anaheim": 24,
    "Atlanta Thrashers": 11,
    "Phoenix Coyotes": 53,
    "Hartford Whalers": 12,
    "Minnesota North Stars": 25,
    "Quebec Nordiques": 21,
    "Chicago Black Hawks": 16,
}

# ---------------------------------------------------------------------------
# coletti: ESPN team ID → NHL API team ID
# Mapping derived from coletti's (team_id, team_name) pairs.
# ---------------------------------------------------------------------------
COLETTI_TEAM_ID_MAP: dict[int, int] = {
    1: 6,       # Boston Bruins
    2: 7,       # Buffalo Sabres
    3: 20,      # Calgary Flames
    4: 16,      # Chicago Blackhawks
    5: 17,      # Detroit Red Wings
    6: 22,      # Edmonton Oilers
    7: 12,      # Carolina Hurricanes
    8: 26,      # Los Angeles Kings
    9: 25,      # Dallas Stars
    10: 8,      # Montreal Canadiens
    11: 1,      # New Jersey Devils
    12: 2,      # New York Islanders
    13: 3,      # New York Rangers
    14: 9,      # Ottawa Senators
    15: 4,      # Philadelphia Flyers
    16: 5,      # Pittsburgh Penguins
    17: 21,     # Colorado Avalanche
    18: 28,     # San Jose Sharks
    19: 19,     # St. Louis Blues
    20: 14,     # Tampa Bay Lightning
    21: 10,     # Toronto Maple Leafs
    22: 23,     # Vancouver Canucks
    23: 15,     # Washington Capitals
    25: 24,     # Anaheim Ducks
    26: 13,     # Florida Panthers
    27: 18,     # Nashville Predators
    28: 52,     # Winnipeg Jets
    29: 29,     # Columbus Blue Jackets
    30: 30,     # Minnesota Wild
    37: 54,     # Vegas Golden Knights
    124292: 55, # Seattle Kraken
    129764: 59, # Utah Hockey Club
}

# ---------------------------------------------------------------------------
# mexwell: MoneyPuck abbreviation → standard NHL abbreviation
# Only entries that differ; identity mappings are resolved at runtime.
# ---------------------------------------------------------------------------
MONEYPUCK_ABBREV_MAP: dict[str, str] = {
    "L.A": "LAK",
    "N.J": "NJD",
    "S.J": "SJS",
    "T.B": "TBL",
}


def normalize_moneypuck_abbrev(abbrev: str) -> str:
    """Convert MoneyPuck abbreviation to standard NHL abbreviation."""
    return MONEYPUCK_ABBREV_MAP.get(abbrev, abbrev)
