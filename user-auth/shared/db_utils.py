import hashlib
import os
import secrets

import pyodbc


def get_db_connection():
    """Create database connection"""
    conn_str = os.environ.get("SqlConnectionString")
    # Fix double curly braces if present (from Azure portal escaping)
    conn_str = conn_str.replace("{{", "{").replace("}}", "}")
    # Convert True/False to yes/no for ODBC compatibility
    conn_str = conn_str.replace("Encrypt=True", "Encrypt=yes")
    conn_str = conn_str.replace("Encrypt=False", "Encrypt=no")
    conn_str = conn_str.replace(
        "TrustServerCertificate=True", "TrustServerCertificate=yes"
    )
    conn_str = conn_str.replace(
        "TrustServerCertificate=False", "TrustServerCertificate=no"
    )
    conn_str = conn_str.replace(
        "MultipleActiveResultSets=True", "MultipleActiveResultSets=yes"
    )
    conn_str = conn_str.replace(
        "MultipleActiveResultSets=False", "MultipleActiveResultSets=no"
    )
    # Add ODBC driver to connection string if not present
    if "Driver=" not in conn_str:
        conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};" + conn_str
    return pyodbc.connect(conn_str, autocommit=False)


def hash_password(password, salt=None):
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return pwd_hash.hex(), salt


def verify_password(password, password_hash, salt):
    """Verify password against hash"""
    pwd_hash, _ = hash_password(password, salt)
    return pwd_hash == password_hash


def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)
