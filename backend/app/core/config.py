from dotenv import load_dotenv
import os

# charge le fichier environnement .env
loaded = load_dotenv()
print(f"[CONFIG] load_dotenv() a trouvé .env ? {loaded}")
print(f"[CONFIG] OPENROUTER_API_KEY = |{os.getenv('OPENROUTER_API_KEY', 'NON_TROUVÉ')}|")
print(f"[CONFIG] OPENROUTER_MODEL  = |{os.getenv('OPENROUTER_MODEL', 'NON_TROUVÉ')}|")

# ─── Dify ───────────────────────────────────────────────

DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
DIFY_USER = os.getenv("DIFY_USER", "")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME or "noreply@aidfinder.local")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ─── Qwen (fallback LLM) ──────────────────────────────────────────────
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_API_URL = os.getenv(
    "QWEN_API_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
QWEN_TIMEOUT_SECONDS = int(os.getenv("QWEN_TIMEOUT_SECONDS", "30"))
QWEN_MAX_TOKENS = int(os.getenv("QWEN_MAX_TOKENS", "700"))
QWEN_TEMPERATURE = float(os.getenv("QWEN_TEMPERATURE", "0.2"))

# ─── OpenRouter (primary LLM) ─────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL",
    "https://openrouter.ai/api/v1/chat/completions",
)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b:free")
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "700"))
OPENROUTER_TEMPERATURE = float(os.getenv("OPENROUTER_TEMPERATURE", "0.2"))
OPENROUTER_TIMEOUT_SECONDS = int(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30"))
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5173")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "AidFinder")

_default_cors_origins = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_cors_origins).split(",")
    if origin.strip()
]

# Autorise le frontend servi depuis une IP privée (réseau local) sur le port Vite.
CORS_ORIGIN_REGEX = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"http://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}):5173",
)
