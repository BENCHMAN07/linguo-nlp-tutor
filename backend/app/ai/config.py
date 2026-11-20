from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class AIConfig:
    api_key: str
    base_url: str
    model_main: str
    model_fast: str
    enabled: bool
    daily_budget: int
    rate_per_minute: int

def load_config() -> AIConfig:
    key=os.getenv("GROQ_API_KEY", "").strip()
    enabled=os.getenv("AI_ENABLED", "true" if key else "false").strip().lower() in {"1","true","yes","on"}
    return AIConfig(
        api_key=key,
        base_url=os.getenv("GROQ_BASE_URL","https://api.groq.com/openai/v1").rstrip("/"),
        model_main=os.getenv("GROQ_MODEL_MAIN","llama-3.3-70b-versatile").strip(),
        model_fast=os.getenv("GROQ_MODEL_FAST","llama-3.1-8b-instant").strip(),
        enabled=enabled and bool(key),
        daily_budget=max(1,int(os.getenv("AI_DAILY_BUDGET","40"))),
        rate_per_minute=max(1,int(os.getenv("AI_USER_RATE_PER_MINUTE","10"))),
    )
