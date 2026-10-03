from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    app_name: str = "SAHIBEX"
    version: str = "0.1.0"
    environment: str = os.getenv("SAHIBEX_ENV", "development")

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    memory_dir: Path = PROJECT_ROOT / "memory"
    logs_dir: Path = PROJECT_ROOT / "security" / "audit"

    max_task_depth: int = 10
    require_confirmation_for_actions: bool = True
    allow_autonomous_system_changes: bool = False


settings = Settings()
