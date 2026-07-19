from sqlalchemy.orm import Mapped, mapped_column
from database.connection import Base

class Country(Base):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(primary_key=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Country(code={self.code}, name={self.name})>"
