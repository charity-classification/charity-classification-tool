import os

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.environ.get("DATA_DIR", "data/")
COMPLETED_DF = os.path.join(DATA_DIR, "completed.pkl")
TAGS_USED_DF = os.path.join(DATA_DIR, "tags_used.pkl")
ICNPTSO_USED_DF = os.path.join(DATA_DIR, "icnptso_used.pkl")
ALL_CHARITIES_DF = os.path.join(DATA_DIR, "charities_active.pkl")
ALL_CHARITIES_BY_INCOME_DF = os.path.join(DATA_DIR, "charities_by_income.pkl")
ALL_CHARITIES_CSV = os.path.join(DATA_DIR, "charities_active.csv")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TAGS_TABLE_NAME = "Tags - working"
AIRTABLE_ICNPTSO_TABLE_NAME = "ICNPTSO"
AIRTABLE_SAMPLE_TABLE_NAME = "Sample data"
AIRTABLE_SAVE = False
TAGS_FIELD_NAME = "Tags (working)"
ICNPTSO_FIELD_NAME = "ICNPTSO"
DEFAULT_REGEX = r"\b()\b"
