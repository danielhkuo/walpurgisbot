# config.py

import os

# Read the Johan User ID and default/check channel ID from environment variables
JOHAN_USER_ID = int(os.getenv("JOHAN_USER_ID", "474030685577936916"))

# Use the same environment variable for both default and check channel IDs
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID", "797666899558268971"))

# Read the timezone from environment variables, default to 'America/Chicago' if not set
TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
