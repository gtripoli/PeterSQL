import pymysql
import pytest

from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration
from structures.engines.mysql.context import MySQLContext


class TestMySQLContextReliability:
    def test_connect_retries_with_tls_on_auth_error(self, monkeypatch):
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="secret",
            port=3306,
        )
        connection = Connection(
            id=1,
            name="mysql_tls_retry",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )
        context = MySQLContext(connection)
        monkeypatch.setattr(context, "before_connect", lambda *args, **kwargs: None)
        monkeypatch.setattr(context, "after_connect", lambda *args, **kwargs: None)

        calls = []

        class FakeConnection:
            def cursor(self):
                return object()

        def fake_connect(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise pymysql.err.OperationalError(1045, "Access denied")
            return FakeConnection()

        monkeypatch.setattr(pymysql, "connect", fake_connect)

        context.connect(connect_timeout=1)

        assert len(calls) == 2
        assert "ssl" not in calls[0]
        assert "ssl" in calls[1]
        assert connection.configuration.use_tls_enabled is True


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLContext:
    def test_context_connection(self, mysql_session):
        ctx = mysql_session.context
        assert ctx.is_connected is True

    def test_context_execute_query(self, mysql_session):
        ctx = mysql_session.context
        ctx.execute("SELECT 1 as test")
        result = ctx.fetchone()
        assert result["test"] == 1

    def test_context_fetchall(self, mysql_session):
        ctx = mysql_session.context
        ctx.execute("SELECT 1 as val UNION SELECT 2 UNION SELECT 3")
        results = ctx.fetchall()
        assert len(results) == 3

    def test_context_get_server_version(self, mysql_session):
        version = mysql_session.context.get_server_version()
        assert version is not None
        assert len(version) > 0

    def test_context_quote_identifier(self, mysql_session):
        ctx = mysql_session.context
        quote = ctx.IDENTIFIER_QUOTE_CHAR

        assert ctx.quote_identifier("normal") == "normal"
        assert ctx.quote_identifier("with space") == f'{quote}with space{quote}'

    def test_context_transaction(self, mysql_session, mysql_database):
        ctx = mysql_session.context
        db_name = mysql_database.name

        ctx.execute(f"CREATE TABLE {db_name}.test_tx (id INT PRIMARY KEY, name VARCHAR(50))")

        with ctx.transaction() as tx:
            tx.execute(f"INSERT INTO {db_name}.test_tx (id, name) VALUES (1, 'test')")

        ctx.execute(f"SELECT COUNT(*) as cnt FROM {db_name}.test_tx")
        assert ctx.fetchone()["cnt"] == 1

        ctx.execute(f"DROP TABLE {db_name}.test_tx")

    def test_context_databases_list(self, mysql_session):
        ctx = mysql_session.context
        databases = ctx.databases.get_value()
        assert len(databases) > 0
        db_names = [db.name for db in databases]
        assert "information_schema" in db_names
