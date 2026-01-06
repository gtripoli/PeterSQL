import pytest
import tempfile
import os

from structures.session import Session
from structures.engines import SessionEngine
from structures.configurations import CredentialsConfiguration
from structures.engines.mariadb.database import MariaDBDatabase, MariaDBTable


class TestMariaDBTable:
    @pytest.fixture
    def temp_db_path(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name
        yield tmp_path
        os.unlink(tmp_path)

    @pytest.fixture
    def session(self):
        config = CredentialsConfiguration(hostname='localhost', username='user', password='pass', port=3306)
        session = Session(id=1, name='test_session', engine=SessionEngine.MARIADB, configuration=config)
        yield session

    @pytest.fixture
    def database(self, session):
        db = MariaDBDatabase(id=1, name='testdb', context=session.context)
        return db

    def test_table_creation(self, database):
        table = MariaDBTable(
            id=1,
            name='users',
            database=database,
            engine='mariadb'
        )
        assert table.id == 1
        assert table.name == 'users'
        assert table.database.name == database.name
        assert table.engine == 'mariadb'

    def test_table_properties(self, database):
        table = MariaDBTable(
            id=1,
            name='products',
            database=database,
            engine='mariadb',
            total_rows=100,
            auto_increment=101,
            comment='Product table'
        )
        assert table.total_rows == 100
        assert table.auto_increment == 101
        assert table.comment == 'Product table'
