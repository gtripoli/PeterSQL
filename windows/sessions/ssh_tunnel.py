import contextlib
import shutil
import socket
import subprocess
import time

from typing import List
from gettext import gettext as _

from helpers.exceptions import SSHTunnelError
from structures.configurations import CredentialsConfiguration
from structures.session import SSHTunnelConfiguration, Session


class SSHTunnelRunner:
    def __init__(self, session: Session):
        self.session = session

    def ensure(self):
        if not self.session.has_enabled_tunnel():
            return None

        if (process := self.session.tunnel_process) and getattr(process, "poll", lambda: None)() is None:
            return process

        self.session.stop_tunnel()
        return self._start()

    def _start(self):
        if not (config := self.session.ssh_tunnel):
            raise SSHTunnelError("SSH tunnel configuration missing")

        if not isinstance(self.session.configuration, CredentialsConfiguration):
            raise SSHTunnelError(_("SSH tunnel is supported only for server connections"))

        command = self._build_command(config)

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as exc:
            raise SSHTunnelError(_(f"Unable to launch SSH executable: {exc}")) from exc

        try:
            self._wait_for_port("127.0.0.1", config.local_port)
        except TimeoutError as exc:
            process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=2)
            raise SSHTunnelError(_("SSH tunnel not ready")) from exc

        self.session.context.host = "127.0.0.1"
        self.session.context.port = config.local_port
        self.session.set_tunnel_process(process)
        return process

    def _build_command(self, config: SSHTunnelConfiguration) -> List[str]:
        ssh_bin = shutil.which(config.executable) or config.executable

        destination = f"{config.username}@{config.hostname}"
        db_target = self.session.configuration.hostname
        db_port = self.session.configuration.port

        base_command = [
            ssh_bin,
            "-N",
            "-L",
            f"{config.local_port}:{db_target}:{db_port}",
            destination,
            "-p",
            str(config.port or 22),
        ]

        if config.password:
            if sshpass_bin := shutil.which("sshpass"):
                return [sshpass_bin, "-p", config.password, *base_command]
            raise SSHTunnelError(_("sshpass executable required to use SSH password"))

        return base_command

    def _wait_for_port(self, host: str, port: int, timeout: float = 5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                try:
                    sock.connect((host, port))
                    return True
                except OSError:
                    time.sleep(0.2)
        raise TimeoutError(f"Port {port} did not open in time")
