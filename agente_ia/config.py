from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class AppConfig:
    files_root: Path
    output_dir: Path
    llm_provider: str
    openai_api_key: str | None
    openai_model: str
    ollama_base_url: str
    ollama_model: str
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    smtp_from: str | None
    smtp_use_tls: bool
    browser_channel: str | None
    browser_profile_dir: Path
    default_country_code: str


def load_config() -> AppConfig:
    if load_dotenv is not None:
        load_dotenv()
    else:
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    files_root = Path(os.getenv("FILES_ROOT", str(Path.home() / "Documents"))).expanduser()
    output_dir = Path(os.getenv("OUTPUT_DIR", "agent-output")).expanduser()
    browser_profile_dir = Path(os.getenv("BROWSER_PROFILE_DIR", "browser-profile")).expanduser()

    smtp_port_raw = os.getenv("SMTP_PORT", "587").strip()
    smtp_port = int(smtp_port_raw) if smtp_port_raw else 587

    llm_provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if not llm_provider:
        llm_provider = "openai" if os.getenv("OPENAI_API_KEY") else "ollama"

    return AppConfig(
        files_root=files_root,
        output_dir=output_dir,
        llm_provider=llm_provider,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        smtp_host=os.getenv("SMTP_HOST") or None,
        smtp_port=smtp_port,
        smtp_user=os.getenv("SMTP_USER") or None,
        smtp_password=os.getenv("SMTP_PASSWORD") or None,
        smtp_from=os.getenv("SMTP_FROM") or None,
        smtp_use_tls=_to_bool(os.getenv("SMTP_USE_TLS"), True),
        browser_channel=os.getenv("BROWSER_CHANNEL") or None,
        browser_profile_dir=browser_profile_dir,
        default_country_code=os.getenv("DEFAULT_COUNTRY_CODE", "55").strip(),
    )
