from typing import NamedTuple


class CredentialsConfiguration(NamedTuple):
    hostname: str
    username: str
    password: str
    port: int


class SourceConfiguration(NamedTuple):
    filename: str


class SSHTunnelConfiguration(NamedTuple):
    enabled: bool
    executable: str
    hostname: str
    port: int
    username: str
    password: str
    local_port: int

    @property
    def is_enabled(self) -> bool:
        return all([
            self.enabled,
            self.executable,
            self.hostname,
            self.username,
            self.password,
            self.local_port
        ])
