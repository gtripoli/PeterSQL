import signal

from structures.connection import Connection, ConnectionEngine
from structures.ssh_tunnel import SSHTunnel
from structures.configurations import CredentialsConfiguration, SSHTunnelConfiguration
from structures.engines.mysql.context import MySQLContext
from structures.engines.mariadb.context import MariaDBContext


class _FakeTunnel:
    def __init__(self, *args, **kwargs):
        self.local_port = kwargs["local_bind_address"][1] or 4406
        self.call_log: list[str] = kwargs["extra_args"]

    def start(self):
        self.call_log.append("start")

    def stop(self):
        self.call_log.append("stop")


class _FakeProcess:
    def __init__(self):
        self.pid = 999

    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0

    def terminate(self):
        return None


class TestSSHTunnelContextContract:
    def test_mariadb_context_manages_tunnel_lifecycle(self, monkeypatch):
        call_log: list[str] = []
        configuration = CredentialsConfiguration("db.internal", "root", "secret", 3306)
        ssh_tunnel = SSHTunnelConfiguration(
            True,
            "ssh",
            "bastion.internal",
            22,
            "sshuser",
            "sshpass",
            0,
            extra_args=call_log,
        )
        connection = Connection(
            1,
            "mariadb_tunnel",
            ConnectionEngine.MARIADB,
            configuration,
            ssh_tunnel=ssh_tunnel,
        )
        context = MariaDBContext(connection)
        monkeypatch.setattr("structures.engines.context.SSHTunnel", _FakeTunnel)

        context.before_connect()
        assert context.host == "127.0.0.1"
        assert context.port == 4406
        assert call_log == ["start"]

        context.before_disconnect()
        assert context.host == "db.internal"
        assert context.port == 3306
        assert call_log == ["start", "stop"]

    def test_mysql_context_manages_tunnel_lifecycle(self, monkeypatch):
        call_log: list[str] = []
        configuration = CredentialsConfiguration("db.internal", "root", "secret", 3306)
        ssh_tunnel = SSHTunnelConfiguration(
            True,
            "ssh",
            "bastion.internal",
            22,
            "sshuser",
            "sshpass",
            4407,
            extra_args=call_log,
        )
        connection = Connection(
            2,
            "mysql_tunnel",
            ConnectionEngine.MYSQL,
            configuration,
            ssh_tunnel=ssh_tunnel,
        )
        context = MySQLContext(connection)
        monkeypatch.setattr("structures.engines.context.SSHTunnel", _FakeTunnel)

        context.before_connect()
        assert context.host == "127.0.0.1"
        assert context.port == 4407
        assert call_log == ["start"]

        context.before_disconnect()
        assert context.host == "db.internal"
        assert context.port == 3306
        assert call_log == ["start", "stop"]


class TestSSHTunnelStopContract:
    def test_mariadb_disconnect_stops_active_tunnel(self):
        call_log: list[str] = []
        configuration = CredentialsConfiguration("db.internal", "root", "secret", 3306)
        connection = Connection(
            3,
            "mariadb_disconnect",
            ConnectionEngine.MARIADB,
            configuration,
        )
        context = MariaDBContext(connection)

        class FakeActiveTunnel:
            def stop(self):
                call_log.append("stop")

        context._ssh_tunnel = FakeActiveTunnel()
        context.disconnect()

        assert call_log == ["stop"]
        assert context._ssh_tunnel is None

    def test_ssh_tunnel_stop_terminates_posix_process_group(self, monkeypatch):
        kill_calls: list[tuple[int, int]] = []
        tunnel = SSHTunnel("bastion.internal")
        tunnel._process = _FakeProcess()

        monkeypatch.setattr("os.killpg", lambda pid, sig: kill_calls.append((pid, sig)))
        monkeypatch.setattr("os.name", "posix", raising=False)

        tunnel.stop()

        assert kill_calls == [(999, signal.SIGTERM)]
        assert tunnel._process is None

    def test_ssh_tunnel_stop_returns_when_process_is_missing(self):
        tunnel = SSHTunnel("bastion.internal")
        tunnel._process = None

        tunnel.stop()

        assert tunnel._process is None