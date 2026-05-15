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
