import re
from typing import Optional

import keyring

SERVICE_NAME = "PeterSQL"

_LEGACY_NUMERIC_ID_PATTERN = re.compile(r"^[0-9]+$")


def _database_password_key(secret_id: str) -> str:
    return f"connection:{secret_id}:database_password"


def _ssh_password_key(secret_id: str) -> str:
    return f"connection:{secret_id}:ssh_password"


def _is_legacy_numeric_id(secret_id: Optional[str]) -> bool:
    if secret_id is None:
        return False
    return bool(_LEGACY_NUMERIC_ID_PATTERN.match(secret_id))


def get_database_password(secret_id: str) -> Optional[str]:
    key = _database_password_key(secret_id)
    value = keyring.get_password(SERVICE_NAME, key)
    return value if value else None


def set_database_password(secret_id: str, password: Optional[str]) -> None:
    key = _database_password_key(secret_id)
    if password is None or password == "":
        delete_database_password(secret_id)
        return

    keyring.set_password(SERVICE_NAME, key, password)


def delete_database_password(secret_id: str) -> None:
    key = _database_password_key(secret_id)
    try:
        keyring.delete_password(SERVICE_NAME, key)
    except keyring.errors.PasswordDeleteError:
        pass


def get_ssh_password(secret_id: str) -> Optional[str]:
    key = _ssh_password_key(secret_id)
    value = keyring.get_password(SERVICE_NAME, key)
    return value if value else None


def set_ssh_password(secret_id: str, password: Optional[str]) -> None:
    key = _ssh_password_key(secret_id)
    if password is None or password == "":
        delete_ssh_password(secret_id)
        return

    keyring.set_password(SERVICE_NAME, key, password)


def delete_ssh_password(secret_id: str) -> None:
    key = _ssh_password_key(secret_id)
    try:
        keyring.delete_password(SERVICE_NAME, key)
    except keyring.errors.PasswordDeleteError:
        pass
