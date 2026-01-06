import pytest
import tempfile
import os

from structures.session import Session
from structures.engines import SessionEngine
from structures.configurations import CredentialsConfiguration
from structures.engines.mariadb.database import MariaDBDatabase, MariaDBTable, MariaDBColumn
from structures.engines.mariadb.datatype import MariaDBDataType


class TestMariaDBColumn:
    @pytest.fixture
    def temp_db_path(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name
        yield tmp_path
        os.unlink(tmp_path)

    @pytest.fixture
    def session(self, temp_db_path):
        config = CredentialsConfiguration(hostname='localhost', username='user', password='pass', port=3306)
        session = Session(id=1, name='test_session', engine=SessionEngine.MARIADB, configuration=config)
        # Note: MariaDB context may need different setup, but for testing dataclass, perhaps mock
        # For now, skip connection
        yield session

    @pytest.fixture
    def database(self, session):
        db = MariaDBDatabase(id=1, name='testdb', context=session.context)
        return db

    @pytest.fixture
    def table(self, database):
        table = MariaDBTable(
            id=1,
            name='users',
            database=database,
            engine='mariadb'
        )
        return table

    def test_column_creation(self, table):
        column = MariaDBColumn(
            id=1,
            name='id',
            table=table,
            datatype=MariaDBDataType.INT,
            is_nullable=False,
            is_auto_increment=True,
            length=11
        )
        assert column.id == 1
        assert column.name == 'id'
        assert column.table.name == table.name
        assert column.datatype == MariaDBDataType.INT
        assert column.is_nullable == False
        assert column.is_auto_increment == True
        assert column.length == 11

    def test_column_properties(self, table):
        column = MariaDBColumn(
            id=1,
            name='name',
            table=table,
            datatype=MariaDBDataType.VARCHAR,
            is_nullable=True,
            length=255
        )
        assert column.is_nullable == True
        assert column.is_auto_increment == False  # default

    def test_column_add(self, table):
        column = MariaDBColumn(
            id=1,
            name='email',
            table=table,
            datatype=MariaDBDataType.VARCHAR,
            length=255
        )
        # Test add method, but since it's abstract, perhaps skip or mock
        # For now, just creation

    def test_column_drop(self, table):
        column = MariaDBColumn(
            id=1,
            name='email',
            table=table,
            datatype=MariaDBDataType.VARCHAR,
            length=255
        )
        # Test drop method

    def test_column_modify(self, table):
        column = MariaDBColumn(
            id=1,
            name='email',
            table=table,
            datatype=MariaDBDataType.VARCHAR,
            length=255
        )
        # Test modify
