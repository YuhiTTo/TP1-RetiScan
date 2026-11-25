from getpass import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.account import Account


def create_admin():
    print("=== Creación del administrador inicial de RetiScan ===")

    email = input("Correo del administrador: ").strip().lower()
    nombre = input("Nombre mostrado: ").strip()
    password = getpass("Contraseña: ")
    password_confirmation = getpass("Confirmar contraseña: ")

    if not email:
        print("El correo es obligatorio.")
        return

    if not nombre:
        print("El nombre mostrado es obligatorio.")
        return

    if len(password) < 8:
        print("La contraseña debe contener al menos 8 caracteres.")
        return

    if password != password_confirmation:
        print("Las contraseñas no coinciden.")
        return

    db = SessionLocal()

    try:
        existing_account = db.execute(
            select(Account).where(
                Account.correo_electronico == email
            )
        ).scalar_one_or_none()

        if existing_account:
            print("Ya existe una cuenta con ese correo electrónico.")
            return

        admin = Account(
            id_establecimiento=None,
            correo_electronico=email,
            password_hash=hash_password(password),
            tipo_cuenta="ADMIN",
            nombre_mostrado=nombre,
            estado=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print()
        print("Administrador creado correctamente.")
        print(f"ID: {admin.id_cuenta}")
        print(f"Correo: {admin.correo_electronico}")
        print(f"Tipo de cuenta: {admin.tipo_cuenta}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()