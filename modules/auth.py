
import hashlib
import hmac
import secrets

from modules.database import (
    create_user,
    get_user_by_email,
    admin_exists
)


ITERATIONS = 600000


def hash_password(password):
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS
    ).hex()

    return f"pbkdf2_sha256${ITERATIONS}${salt}${password_hash}"


def verify_password(password, stored_hash):
    try:
        algorithm, iterations, salt, original_hash = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations)
        ).hex()

        return hmac.compare_digest(new_hash, original_hash)

    except (ValueError, TypeError):
        return False


def create_initial_admin(name, email, password):
    if admin_exists():
        return False, "Admin account already exists."

    if not name.strip() or not email.strip():
        return False, "Name and email are required."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    password_hash = hash_password(password)

    success = create_user(
        name,
        email,
        password_hash,
        role="admin"
    )

    if success:
        return True, "Admin account created successfully."

    return False, "This email is already registered."


def register_user(name, email, password):
    if not name.strip() or not email.strip():
        return False, "Name and email are required."

    if "@" not in email or "." not in email:
        return False, "Enter a valid email address."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    password_hash = hash_password(password)

    success = create_user(
        name,
        email,
        password_hash,
        role="user"
    )

    if success:
        return True, "Registration successful."

    return False, "This email is already registered."


def authenticate_user(email, password):
    user = get_user_by_email(email)

    if user is None:
        return None

    if not user["is_active"]:
        return None

    if verify_password(password, user["password_hash"]):
        return user

    return None
