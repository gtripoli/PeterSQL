import atexit
import os
import shutil
import signal
import socket
import subprocess
import time

from typing import List, Optional, Tuple

import gettext as _

from helpers.exceptions import SSHTunnelError
from helpers.logger import logger


class SSHTunnel:
    def __init__(self, ssh_hostname: str, ssh_port: int = 22, /,
                 ssh_username: Optional[str] = None, ssh_password: Optional[str] = None,
                 remote_port: int = 3306, local_bind_address: Tuple[str, int] = ('localhost', 0),
                 ssh_executable: str = 'ssh',
                 identity_file: Optional[str] = None,
                 extra_args: Optional[List[str]] = None):

        self.ssh_hostname = ssh_hostname
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password

        # self.remote_host, self.remote_port = remote_bind_address
        self.remote_port = remote_port
        self.local_address, self.local_port = local_bind_address

        self.ssh_executable = ssh_executable
        self.identity_file = identity_file
        self.extra_args = extra_args or []
        self._process: Optional[subprocess.Popen] = None

    def __enter__(self):
        self.start()
        return self.local_port

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self, timeout: float = 5.0):
        if self.local_port == 0:
            self.local_port = self._find_free_port(self.local_address)

        self._check_ssh_available()

        destination = []
        if self.ssh_username:
            destination.append(f"{self.ssh_username}@")
        destination.append(self.ssh_hostname)

        cmd = [
            self.ssh_executable,
            "-N",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-L", f"{self.local_address}:{self.local_port}:127.0.0.1:{self.remote_port}",
            "-p", str(self.ssh_port),
        ]

        if self.identity_file:
            cmd += ["-i", self.identity_file]

        cmd += self.extra_args
        cmd.append(''.join(destination))

        base_cmd = cmd

        if self.ssh_password:
            if sshpass_bin := shutil.which("sshpass"):
                cmd = [sshpass_bin, "-p", self.ssh_password] + base_cmd
            else:
                raise SSHTunnelError("sshpass executable required to use SSH password")

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )

        self._wait_until_ready(timeout)

        atexit.register(self.stop)

    def stop(self):
        if not self._process:
            return

        if os.name != "nt":
            os.killpg(self._process.pid, signal.SIGTERM)
        else:
            self._process.terminate()

        try:
            self._process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._process.kill()

        self._process = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    # ---------- internals ----------

    @staticmethod
    def _check_ssh_available():
        if not shutil.which("ssh"):
            raise SSHTunnelError(_("OpenSSH client not found."))

    def _find_free_port(self, host: str) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, 0))
            return s.getsockname()[1]

    def _wait_until_ready(self, timeout: float):
        deadline = time.time() + timeout
        while time.time() <= deadline:
            logger.debug(f"Checking port {self.local_address}:{self.local_port} is ready...")

            # Check if port is open
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                try:
                    sock.connect((self.local_address, self.local_port))
                    return
                except OSError:
                    pass
            time.sleep(0.1)
        raise TimeoutError(f"Port {self.local_port} did not open in time")
