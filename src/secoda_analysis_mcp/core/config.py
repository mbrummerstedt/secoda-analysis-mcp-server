import os

# --------------------------------
# Configuration
# --------------------------------

API_URL = os.getenv("API_URL", "https://app.secoda.co/api/v1/")
API_TOKEN = os.getenv("API_TOKEN")

# Optional: pin a Secoda AI persona for all ai_chat calls.
# Find persona IDs in Secoda → Settings → AI → Personas.
AI_PERSONA_ID = os.getenv("AI_PERSONA_ID")

# Base URL for endpoints outside the /api/v1/ prefix (e.g., /ai/embedded_prompt/)
_base = API_URL.rstrip("/")
EAPI_BASE_URL = _base[: -len("/api/v1")] if _base.endswith("/api/v1") else _base
