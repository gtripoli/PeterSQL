from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration


class TestSQLiteContext:
    def test_context_creation(self):
        config = SourceConfiguration(filename=":memory:")
        connection = Connection(
            id=1,
            name="test_connection",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )
        session = Session(connection=connection)

        assert session.context is not None
        assert session.context.connection == connection
        assert session.context.filename == ":memory:"

    def test_context_connection(self):
        config = SourceConfiguration(filename=":memory:")
        connection = Connection(
            id=1,
            name="test_connection",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )
        session = Session(connection=connection)

        session.context.connect()
        assert session.context._connection is not None

        session.context.execute("SELECT 1 as test")
        result = session.context.fetchone()
        assert result["test"] == 1

        session.context.disconnect()
        assert session.context._connection is None

    def test_context_fetchone(self, sqlite_session):
        """Test fetchone method."""
        ctx = sqlite_session.context

        with ctx.transaction() as transaction:
            transaction.execute("CREATE TABLE test_fetchone (id INTEGER PRIMARY KEY, name TEXT)")
            transaction.execute("INSERT INTO test_fetchone (name) VALUES ('a')")
            transaction.execute("INSERT INTO test_fetchone (name) VALUES ('b')")

        with ctx.transaction() as transaction:
            transaction.execute("SELECT COUNT(*) as cnt FROM test_fetchone")
            result = transaction.fetchone()
            assert result["cnt"] == 2

        with ctx.transaction() as transaction:
            transaction.execute("DROP TABLE test_fetchone")

    def test_context_fetchall(self, sqlite_session):
        """Test fetchall method."""
        ctx = sqlite_session.context

        with ctx.transaction() as transaction:
            transaction.execute("CREATE TABLE test_fetch (id INTEGER PRIMARY KEY, val TEXT)")
            transaction.execute("INSERT INTO test_fetch (val) VALUES ('x'), ('y'), ('z')")

        with ctx.transaction() as transaction:
            transaction.execute("SELECT val FROM test_fetch ORDER BY val")
            results = transaction.fetchall()
            assert len(results) == 3
            assert results[0]["val"] == "x"
            assert results[2]["val"] == "z"

        with ctx.transaction() as transaction:
            transaction.execute("DROP TABLE test_fetch")

    def test_context_transaction(self, sqlite_session):
        """Test transaction context manager."""
        ctx = sqlite_session.context

        with ctx.transaction() as transaction:
            transaction.execute("CREATE TABLE test_tx (id INTEGER PRIMARY KEY, name TEXT)")

        with ctx.transaction() as transaction:
            transaction.execute("INSERT INTO test_tx (name) VALUES ('test')")

        with ctx.transaction() as transaction:
            transaction.execute("SELECT COUNT(*) as cnt FROM test_tx")
            assert transaction.fetchone()["cnt"] == 1

        with ctx.transaction() as transaction:
            transaction.execute("DROP TABLE test_tx")

    def test_context_get_server_version(self, sqlite_session):
        """Test getting server version."""
        version = sqlite_session.context.get_server_version()
        assert version is not None
        assert len(version) > 0

    def test_context_build_sql_safe_name(self, sqlite_session):
        """Test building SQL safe names uses IDENTIFIER_QUOTE."""
        ctx = sqlite_session.context
        quote = ctx.IDENTIFIER_QUOTE

        # Simple names don't need quoting
        assert ctx.build_sql_safe_name("normal") == "normal"
        # Names with spaces are quoted using IDENTIFIER_QUOTE
        assert ctx.build_sql_safe_name("with space") == f'{quote}with space{quote}'
