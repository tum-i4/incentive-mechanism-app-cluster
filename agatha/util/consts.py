"""Const values."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# base urls
CONFIG_APP_BASE_URL = "/app/config"
SURVEY_APP_BASE_URL = "/app/survey"
INCENTIVE_API_BASE_URL = "/incentives"

# auth cookie related consts
AUTH_KEY = "agatha-auth"
DEV_USER = "demo@example.com"
AUTH_AGE = 3600
