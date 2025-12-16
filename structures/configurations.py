from typing import NamedTuple, Optional


class CredentialsConfiguration(NamedTuple):
    hostname: str
    username: str
    password: Optional[str]
    port: int


class SourceConfiguration(NamedTuple):
    filename: str


class SSHTunnelConfiguration(NamedTuple):
    enabled: bool
    executable: str
    hostname: str
    port: int
    username: Optional[str]
    password: Optional[str]
    local_port: int

    @property
    def is_enabled(self) -> bool:
        return all([
            self.enabled,
            self.executable,
            self.hostname,
            self.local_port
        ])
