from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.account import Account
from app.repositories.account_repository import get_account_by_email


def authenticate_account(
    db: Session,
    email: str,
    password: str
) -> Account | None:

    account = get_account_by_email(
        db=db,
        email=email
    )

    if account is None:
        return None

    if not account.estado:
        return None

    if not verify_password(
        password,
        account.password_hash
    ):
        return None

    return account