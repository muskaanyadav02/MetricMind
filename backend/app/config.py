"""Application configuration for the MetricMind backend.

Every value is sourced from environment variables (optionally via a local
``.env`` file). Nothing in this module connects to a database or validates
credentials eagerly: the application must stay importable and testable on a
machine that has no Snowflake access at all. Credential presence is only ever
*reported* (see :attr:`Settings.warehouse_configured`) or checked at the moment
a real connection is attempted.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

# Warehouse backends. Snowflake is implemented; Cube is a documented placeholder
# for the semantic layer the Data & Semantic Engineering work will add later.
WAREHOUSE_BACKEND_SNOWFLAKE = "snowflake"
WAREHOUSE_BACKEND_CUBE = "cube"
SUPPORTED_WAREHOUSE_BACKENDS = (WAREHOUSE_BACKEND_SNOWFLAKE, WAREHOUSE_BACKEND_CUBE)


class Settings(BaseSettings):
    """Runtime settings, populated from the environment."""

    model_config = SettingsConfigDict(
        # An absolute path, so the file is found regardless of the working
        # directory the server is started from - and so a stray .env elsewhere
        # in the tree is never picked up.
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -- Application ------------------------------------------------------
    app_name: str = "MetricMind Backend"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # -- CORS -------------------------------------------------------------
    # Comma-separated. Defaults cover the two ports a React/Next.js dev server
    # most commonly uses. The frontend framework is not yet decided in the
    # repository (docs/PROJECT_PLAN.md says "React or Next.js"), so this is
    # deliberately configuration rather than a hardcoded origin.
    cors_allow_origins: str = "http://localhost:3000,http://localhost:5173"
    cors_allow_credentials: bool = True

    # -- Timeouts / limits ------------------------------------------------
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    warehouse_timeout_seconds: float = Field(default=30.0, gt=0)
    max_result_rows: int = Field(default=500, ge=1, le=10000)
    default_result_rows: int = Field(default=100, ge=1, le=10000)

    # -- Warehouse selection ---------------------------------------------
    warehouse_backend: str = WAREHOUSE_BACKEND_SNOWFLAKE

    # -- Snowflake --------------------------------------------------------
    # Database/schema/warehouse defaults reflect the objects documented in
    # docs/data_dictionary.md ("Snowflake Objects"): database METRICMIND,
    # schemas RAW/STAGING/INTERMEDIATE/MART, warehouse METRICMIND_WH.
    # Credentials have no defaults on purpose: they must never be committed.
    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_password: Optional[str] = None
    snowflake_role: Optional[str] = None
    snowflake_warehouse: Optional[str] = None
    snowflake_database: str = "METRICMIND"
    snowflake_schema: str = "MART"
    snowflake_authenticator: Optional[str] = None

    # -- Cube.dev (semantic layer, not implemented yet) --------------------
    cube_api_url: Optional[str] = None
    cube_api_token: Optional[str] = None

    # -- Derived helpers ---------------------------------------------------
    @property
    def cors_origins(self) -> List[str]:
        """CORS origins as a list, ignoring blanks."""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def warehouse_configured(self) -> bool:
        """Whether enough Snowflake settings exist to attempt a connection.

        This is a *presence* check only. It never validates the credentials and
        never opens a connection.
        """
        if self.warehouse_backend == WAREHOUSE_BACKEND_CUBE:
            return bool(self.cube_api_url and self.cube_api_token)
        return bool(
            self.snowflake_account
            and self.snowflake_user
            and self.snowflake_password
            and self.snowflake_warehouse
        )

    @property
    def missing_warehouse_settings(self) -> List[str]:
        """Names (only) of the settings required for the chosen backend."""
        if self.warehouse_backend == WAREHOUSE_BACKEND_CUBE:
            required = {"CUBE_API_URL": self.cube_api_url, "CUBE_API_TOKEN": self.cube_api_token}
        else:
            required = {
                "SNOWFLAKE_ACCOUNT": self.snowflake_account,
                "SNOWFLAKE_USER": self.snowflake_user,
                "SNOWFLAKE_PASSWORD": self.snowflake_password,
                "SNOWFLAKE_WAREHOUSE": self.snowflake_warehouse,
            }
        return [name for name, value in required.items() if not value]

    @property
    def safe_warehouse_summary(self) -> dict:
        """Non-secret description of the warehouse target, for health output.

        Deliberately excludes account, user, password and role.
        """
        return {
            "backend": self.warehouse_backend,
            "database": self.snowflake_database,
            "schema": self.snowflake_schema,
            "configured": self.warehouse_configured,
            "missing_settings": self.missing_warehouse_settings,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    ``lru_cache`` keeps this cheap and lets tests clear it via
    ``get_settings.cache_clear()`` after mutating the environment.
    """
    return Settings()


def reset_settings_cache() -> None:
    """Drop the cached settings so the environment is re-read (test helper)."""
    get_settings.cache_clear()


__all__ = [
    "Settings",
    "get_settings",
    "reset_settings_cache",
    "BACKEND_DIR",
    "ENV_FILE",
    "WAREHOUSE_BACKEND_SNOWFLAKE",
    "WAREHOUSE_BACKEND_CUBE",
    "SUPPORTED_WAREHOUSE_BACKENDS",
]
