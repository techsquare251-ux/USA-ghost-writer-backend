from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Liblit Backend"
    environment: str = "local"
    database_url: str
    frontend_url: str = "http://localhost:3000"

    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_pass: str
    smtp_from: str
    smtp_secure: bool = False
    smtp_timeout_seconds: int = 30
    admin_emails: str

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None
    google_calendar_id: str = "primary"

    admin_api_token: str | None = None

    portfolio_cover_upload_dir: str | None = None
    portfolio_cover_public_path: str = "/books"

    trustpilot_api_base_url: str = "https://api.trustpilot.com"
    trustpilot_business_unit_id: str | None = None
    trustpilot_api_key: str | None = None
    trustpilot_client_id: str | None = None
    trustpilot_client_secret: str | None = None
    trustpilot_access_token: str | None = None
    trustpilot_cache_ttl_seconds: int = 3600
    trustpilot_default_limit: int = 5

    meeting_duration_minutes: int = 15
    meeting_buffer_minutes: int = 0
    meeting_timezone: str = "UTC"
    business_hours_start: str = "00:00"
    business_hours_end: str = "23:59"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def admin_email_list(self) -> list[str]:
        return [email.strip() for email in self.admin_emails.split(",") if email.strip()]


settings = Settings()
