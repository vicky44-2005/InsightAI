
from modules.database import initialize_database, admin_exists
from modules.auth import hash_password, verify_password

print("Testing InsightAI Authentication")

initialize_database()

print("Database initialized successfully.")

password = "TestPassword123"

hashed = hash_password(password)

print("Password hashing:", "PASSED" if hashed != password else "FAILED")

print(
    "Password verification:",
    "PASSED" if verify_password(password, hashed) else "FAILED"
)

print("Admin already exists:", admin_exists())

print("Authentication test completed.")
