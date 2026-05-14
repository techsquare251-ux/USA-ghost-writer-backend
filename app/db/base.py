from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import contact  # noqa: E402,F401
from app.models import oauth_token  # noqa: E402,F401
