import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

# NHL API base URLs
NHL_API_WEB = "https://api-web.nhle.com/v1"
NHL_API_STATS = "https://api.nhle.com/stats/rest/en"

# Seasons range (salary cap era)
FIRST_SEASON = 20052006
LAST_SEASON = 20242025
