"""Create the initial admin user. Run once after database setup."""
import sys

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import User


def seed():
    db = SessionLocal()
    email = input("Admin email: ").strip()
    password = input("Admin password: ").strip()
    name = input("Full name: ").strip()

    if db.query(User).filter(User.email == email).first():
        print(f"User {email} already exists.")
        sys.exit(1)

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=name,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    print(f"Admin user '{email}' created successfully.")
    db.close()


if __name__ == "__main__":
    seed()
