from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account


def get_account_by_email(
    db: Session,
    email: str
) -> Account | None:

    statement = select(Account).where(
        func.lower(Account.correo_electronico)
        == email.strip().lower()
    )

    return db.execute(
        statement
    ).scalar_one_or_none()