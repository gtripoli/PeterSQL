import pytest
import tempfile
import os

from structures.session import Connection
from structures.engines import ConnectionEngine
from structures.configurations import CredentialsConfiguration
from structures.engines.mysql.database import MySQLDatabase, MySQLTable, MySQLColumn
from structures.engines.mysql.datatype import MySQLDataType


class TestMySQLColumn:
    @pytest.fixture
    def temp_db_path(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name
        yield tmp_path
        os.unlink(tmp_path)

    @pytest.fixture
    def session(self):
        config = CredentialsConfiguration(hostname='localhost', username='user', password='pass', port=3306)
        session = Connection(id=1, name='test_session', engine=ConnectionEngine.MYSQL, configuration=config)
        yield session

    @pytest.fixture
    def database(self, session):
        db = MySQLDatabase(id=1, name='testdb', context=session.context)
        return db

    @pytest.fixture
    def table(self, database):
        table = MySQLTable(
            id=1,
            name='users',
            database=database,
            engine='mysql'
        )
        return table

    def test_column_creation(self, table):
        column = MySQLColumn(
            id=1,
            name='id',
            table=table,
            datatype=MySQLDataType.INT,
            is_nullable=False,
            is_auto_increment=True,
            length=11
        )
        assert column.id == 1
        assert column.name == 'id'
        assert column.table.name == table.name
        assert column.datatype == MySQLDataType.INT
        assert column.is_nullable == False
        assert column.is_auto_increment == True
        assert column.length == 11

    def test_column_properties(self, table):
        column = MySQLColumn(
            id=1,
            name='name',
            table=table,
            datatype=MySQLDataType.VARCHAR,
            is_nullable=True,
            length=255
        )
        assert column.is_nullable == True
        assert column.is_auto_increment == False  # default
