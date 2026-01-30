import pytest

from structures.engines.sqlite.datatype import SQLiteDataType
from structures.session import Connection
from structures.engines import ConnectionEngine
from structures.configurations import SourceConfiguration
from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteForeignKey, SQLiteColumn


class TestSQLiteForeignKey:
    @pytest.fixture
    def database(self, sqlite_session):
        db = SQLiteDatabase(id=1, name='main', context=sqlite_session.context)
        return db

    @pytest.fixture
    def table(self, database):
        table = SQLiteTable(
            id=1,
            name='users',
            database=database,
            engine='sqlite'
        )
        # Add columns for table creation
        id_col = SQLiteColumn(id=1, name='id', table=table, datatype=SQLiteDataType.INTEGER, is_auto_increment=True, is_nullable=False)
        name_col = SQLiteColumn(id=2, name='name', table=table, datatype=SQLiteDataType.TEXT, is_nullable=False)
        table.columns._value = [id_col, name_col]
        table.columns._loaded = True
        # Create the table in DB for integration tests
        table.create()
        return table

    def test_foreign_key_creation(self, table):
        fk = SQLiteForeignKey(
            id=1,
            name='fk_users_parent',
            table=table,
            columns=['parent_id'],
            reference_table='parents',
            reference_columns=['id'],
            on_update='CASCADE',
            on_delete='SET NULL'
        )
        assert fk.id == 1
        assert fk.name == 'fk_users_parent'
        assert fk.table.name == table.name
        assert fk.columns == ['parent_id']
        assert fk.reference_table == 'parents'
        assert fk.reference_columns == ['id']
        assert fk.on_update == 'CASCADE'
        assert fk.on_delete == 'SET NULL'

    def test_foreign_key_equality(self, table):
        fk1 = SQLiteForeignKey(
            id=1,
            name='fk_users_parent',
            table=table,
            columns=['parent_id'],
            reference_table='parents',
            reference_columns=['id'],
            on_update='CASCADE',
            on_delete='SET NULL'
        )
        fk2 = SQLiteForeignKey(
            id=1,
            name='fk_users_parent',
            table=table,
            columns=['parent_id'],
            reference_table='parents',
            reference_columns=['id'],
            on_update='CASCADE',
            on_delete='SET NULL'
        )
        fk3 = SQLiteForeignKey(
            id=2,
            name='fk_users_other',
            table=table,
            columns=['other_id'],
            reference_table='others',
            reference_columns=['id'],
            on_update='RESTRICT',
            on_delete='CASCADE'
        )

        assert fk1.id == fk2.id
        assert fk1.name == fk2.name
        assert fk1.columns == fk2.columns
        assert fk1.reference_table == fk2.reference_table
        assert fk1.reference_columns == fk2.reference_columns
        assert fk1.on_update == fk2.on_update
        assert fk1.on_delete == fk2.on_delete

        assert fk1.id != fk3.id

    def test_foreign_key_is_valid(self, table):
        valid_fk = SQLiteForeignKey(
            id=1,
            name='fk_users_parent',
            table=table,
            columns=['parent_id'],
            reference_table='parents',
            reference_columns=['id'],
            on_update='CASCADE',
            on_delete='SET NULL'
        )
        invalid_fk = SQLiteForeignKey(
            id=2,
            name='',
            table=table,
            columns=[],
            reference_table='',
            reference_columns=[],
            on_update='CASCADE',
            on_delete='SET NULL'
        )

        assert valid_fk.is_valid == True
        assert invalid_fk.is_valid == False

    def test_foreign_key_str(self, table):
        fk = SQLiteForeignKey(
            id=1,
            name='fk_users_parent',
            table=table,
            columns=['parent_id'],
            reference_table='parents',
            reference_columns=['id'],
            on_update='CASCADE',
            on_delete='SET NULL'
        )
        expected_str = "SQLiteForeignKey(id=1, name=fk_users_parent, columns=['parent_id'], reference_table=parents, reference_columns=['id'])"
        assert str(fk) == expected_str
