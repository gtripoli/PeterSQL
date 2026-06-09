from typing import Optional

import keyring

SERVICE_NAME = "PeterSQL"


def _database_password_key(connection_id: int) -> str:
    return f"connection:{connection_id}:database_password"


def _ssh_password_key(connection_id: int) -> str:
    return f"connection:{connection_id}:ssh_password"


def get_database_password(connection_id: int) -> Optional[str]:
    key = _database_password_key(connection_id)
    value = keyring.get_password(SERVICE_NAME, key)
    return value if value else None


def set_database_password(connection_id: int, password: Optional[str]) -> None:
    key = _database_password_key(connection_id)
    if password is None or password == "":
        delete_database_password(connection_id)
        return

    keyring.set_password(SERVICE_NAME, key, password)


def delete_database_password(connection_id: int) -> None:
    key = _database_password_key(connection_id)
    try:
        keyring.delete_password(SERVICE_NAME, key)
    except keyring.errors.PasswordDeleteError:
        pass


def get_ssh_password(connection_id: int) -> Optional[str]:
    key = _ssh_password_key(connection_id)
    value = keyring.get_password(SERVICE_NAME, key)
    return value if value else None


def set_ssh_password(connection_id: int, password: Optional[str]) -> None:
    key = _ssh_password_key(connection_id)
    if password is None or password == "":
        delete_ssh_password(connection_id)
        return

    keyring.set_password(SERVICE_NAME, key, password)


def delete_ssh_password(connection_id: int) -> None:
    key = _ssh_password_key(connection_id)
    try:
        keyring.delete_password(SERVICE_NAME, key)
    except keyring.errors.PasswordDeleteError:
        pass
