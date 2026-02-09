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
        assert session.context.session.connection == connection
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
        ctx.execute("CREATE TABLE test_fetchone (id INTEGER PRIMARY KEY, name TEXT)")
        ctx.execute("INSERT INTO test_fetchone (name) VALUES ('a')")
        ctx.execute("INSERT INTO test_fetchone (name) VALUES ('b')")

        ctx.execute("SELECT COUNT(*) as cnt FROM test_fetchone")
        result = ctx.fetchone()
        assert result["cnt"] == 2

        ctx.execute("DROP TABLE test_fetchone")

    def test_context_fetchall(self, sqlite_session):
        """Test fetchall method."""
        ctx = sqlite_session.context
        ctx.execute("CREATE TABLE test_fetch (id INTEGER PRIMARY KEY, val TEXT)")
        ctx.execute("INSERT INTO test_fetch (val) VALUES ('x'), ('y'), ('z')")

        ctx.execute("SELECT val FROM test_fetch ORDER BY val")
        results = ctx.fetchall()

        assert len(results) == 3
        assert results[0]["val"] == "x"
        assert results[2]["val"] == "z"

        ctx.execute("DROP TABLE test_fetch")

    def test_context_transaction(self, sqlite_session):
        """Test transaction context manager."""
        ctx = sqlite_session.context
        ctx.execute("CREATE TABLE test_tx (id INTEGER PRIMARY KEY, name TEXT)")

        with ctx.transaction() as tx:
            tx.execute("INSERT INTO test_tx (name) VALUES ('test')")

        ctx.execute("SELECT COUNT(*) as cnt FROM test_tx")
        assert ctx.fetchone()["cnt"] == 1

        ctx.execute("DROP TABLE test_tx")

    def test_context_get_server_version(self, sqlite_session):
        """Test getting server version."""
        version = sqlite_session.context.get_server_version()
        assert version is not None
        assert len(version) > 0

    def test_context_build_sql_safe_name(self, sqlite_session):
        """Test building SQL safe names uses QUOTE_IDENTIFIER."""
        ctx = sqlite_session.context
        quote = ctx.QUOTE_IDENTIFIER

        # Simple names don't need quoting
        assert ctx.build_sql_safe_name("normal") == "normal"
        # Names with spaces are quoted using QUOTE_IDENTIFIER
        assert ctx.build_sql_safe_name("with space") == f'{quote}with space{quote}'
