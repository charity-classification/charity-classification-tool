import os

from dotenv import load_dotenv

load_dotenv()

COMPLETED_DF = "data/completed.pkl"
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TAGS_TABLE_NAME = "Tags"
DEFAULT_REGEX = r"\b()\b"
