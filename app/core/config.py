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
    admin_emails: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def admin_email_list(self) -> list[str]:
        return [email.strip() for email in self.admin_emails.split(",") if email.strip()]


settings = Settings()
