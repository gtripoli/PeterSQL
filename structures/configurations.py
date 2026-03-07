from typing import NamedTuple, Optional


class CredentialsConfiguration(NamedTuple):
    hostname: str
    username: str
    password: Optional[str]
    port: int
    use_tls_enabled: bool = False


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
    remote_host: Optional[str] = None
    remote_port: Optional[int] = None
    identity_file: Optional[str] = None
    extra_args: Optional[list[str]] = None

    @property
    def is_enabled(self) -> bool:
        return all(
            [
                self.enabled,
                self.executable,
                self.hostname,
            ]
        )
