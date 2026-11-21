import os
from dotenv import load_dotenv

load_dotenv(override=True)

raw_key = os.getenv("GEMINI_API_KEY", "")

# Strip quotes and whitespace automatically
GEMINI_API_KEY = raw_key.strip().strip('"').strip("'")