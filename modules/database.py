
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "insightai.db"


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection




def initialize_database():
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL UNIQUE,
                file_path TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                column_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        connection.commit()
        print("Database initialized successfully.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def get_user_by_email(email):
    connection = get_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.strip().lower(),)
    ).fetchone()

    connection.close()

    return user


def create_user(name, email, password_hash, role="user"):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (name.strip(), email.strip().lower(), password_hash, role)
        )

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()
       
    
def admin_exists():
    connection = get_connection()

    try:
        admin = connection.execute(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

        return admin is not None

    finally:
        connection.close()



def get_all_users():
    connection = get_connection()

    try:
        users = connection.execute("""
            SELECT id, name, email, role, is_active, created_at
            FROM users
            WHERE role = 'user'
            ORDER BY id DESC
        """).fetchall()

        return users

    finally:
        connection.close()


def update_user_status(user_id, is_active):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            UPDATE users
            SET is_active = ?
            WHERE id = ? AND role = 'user'
        """, (int(is_active), user_id))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def get_user_statistics():
    connection = get_connection()

    try:
        total = connection.execute("""
            SELECT COUNT(*) FROM users WHERE role = 'user'
        """).fetchone()[0]

        active = connection.execute("""
            SELECT COUNT(*) FROM users
            WHERE role = 'user' AND is_active = 1
        """).fetchone()[0]

        inactive = total - active

        return total, active, inactive

    finally:
        connection.close()


def save_dataset_record(
    user_id,
    original_filename,
    stored_filename,
    file_path,
    row_count,
    column_count
):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO datasets (
                user_id,
                original_filename,
                stored_filename,
                file_path,
                row_count,
                column_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            original_filename,
            stored_filename,
            file_path,
            row_count,
            column_count
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_user_datasets(user_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM datasets
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    finally:
        connection.close()


def get_user_dataset(dataset_id, user_id):
    connection = get_connection()

    try:
        return connection.execute("""
            SELECT *
            FROM datasets
            WHERE id = ? AND user_id = ?
        """, (dataset_id, user_id)).fetchone()

    finally:
        connection.close()


def delete_user_dataset_record(dataset_id, user_id):
    connection = get_connection()

    try:
        cursor = connection.execute("""
            DELETE FROM datasets
            WHERE id = ? AND user_id = ?
        """, (dataset_id, user_id))

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()
