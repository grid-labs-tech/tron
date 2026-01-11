#!/usr/bin/env python3
"""
Script to load initial admin user
"""
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.shared.database.database import SessionLocal
from app.users.infra.user_model import User, UserRole
import bcrypt


def load_initial_user():
    """Load initial admin user if it doesn't exist"""
    db: Session = SessionLocal()

    try:
        # Check if admin user already exists (use string directly to avoid enum issues)
        existing_admin = db.query(User).filter(
            User.email == 'admin@example.com'
        ).first()

        # Check if it's admin (compare with string)
        if existing_admin and existing_admin.role == UserRole.ADMIN.value:
            print("✓ Admin user already exists. Skipping creation.")
            return

        # Create password hash using bcrypt directly
        # (avoids compatibility issues with passlib)
        password = 'admin'
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        # Create admin user
        admin_user = User(
            email='admin@example.com',
            hashed_password=hashed_password,
            full_name='Administrator',
            role=UserRole.ADMIN.value,  # Now it's String, works normally
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        # Fetch the created user to display the UUID
        admin_user = db.query(User).filter(User.email == 'admin@example.com').first()

        print("✓ Admin user created successfully!")
        print(f"  Email: admin@example.com")
        print(f"  Password: admin")
        print(f"  UUID: {admin_user.uuid}")

    except Exception as e:
        db.rollback()
        print(f"✗ Error creating admin user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    load_initial_user()

