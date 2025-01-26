# config.py

import os
import pathlib

# ---------------------------
# CENTRALIZED DATABASE PATH
# ---------------------------
BASE_DIR = pathlib.Path(__file__).parent.resolve()
DB_FILE = str(BASE_DIR / "daily_johans.db")

# ---------------------------
# ENVIRONMENT VARIABLES
# ---------------------------
JOHAN_USER_ID = int(os.getenv("JOHAN_USER_ID", "474030685577936916"))
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID", "797666899558268971"))
TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
