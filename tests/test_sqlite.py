import pytest

from structures.configurations import SourceConfiguration
from structures.connection import Connection, ConnectionEngine
from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteColumn, SQLiteRecord, SQLiteIndex
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType


class TestSQLiteIntegration:
    @pytest.fixture
    def session(self):
        config = SourceConfiguration(filename=':memory:')
        session = Connection(id=1, name='test_session', engine=ConnectionEngine.SQLITE, configuration=config)
        session.context.connect()
        yield session
        session.context.disconnect()

    def test_full_database_workflow(self, session):
        # Create database
        db = SQLiteDatabase(id=1, name='main', context=session.context)

        # Create table with columns
        table = SQLiteTable(
            id=1,
            name='users',
            database=db,
            engine='sqlite'
        )

        id_column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=SQLiteDataType.INTEGER,
            is_auto_increment=True,
            is_nullable=False
        )

        name_column = SQLiteColumn(
            id=2,
            name='name',
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=False,
            length=255  # Set length for TEXT column
        )

        table.columns._value = [id_column, name_column]
        table.columns._loaded = True

        # Add primary index
        primary_index = SQLiteIndex(
            id=1,
            name='PRIMARY',
            type=SQLiteIndexType.PRIMARY,
            columns=['id'],
            table=table
        )
        table.indexes._value = [primary_index]
        table.indexes._loaded = True

        # Add table to database
        db.tables._value = [table]
        db.tables._loaded = True

        # Set handlers
        table.get_records_handler = (
            lambda t, f=None, l=1000, o=0, ord=None: session.context.get_records(
                t,
                filters=f,
                limit=l,
                offset=o,
                orders=ord,
            )
        )

        # Check table validity
        assert table.is_valid == True

        # Create table in database using table.create()
        result = table.create()
        assert result == True

        # Check that the table is in the database's tables
        assert len(db.tables.get_value()) == 1
        assert db.tables.get_value()[0].name == 'users'

        # Verify table was created
        result = session.context.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        row = session.context.fetchone()
        assert row['name'] == 'users'

        # Load records
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 0  # No records yet

        # Insert a record using SQLiteRecord
        new_record = SQLiteRecord(
            id=-1,
            table=table,
            values={'name': 'John Doe'}
        )
        result = new_record.insert()
        assert result == True

        # Load records again
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values['name'] == 'John Doe'

        # Test record operations
        record = records[0]
        assert record.is_valid() == True
        assert record.is_new() == False

        # Update the record
        record.values['name'] = 'Jane Doe'
        result = record.update()
        assert result == True

        # Load records and check update
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values['name'] == 'Jane Doe'

        # Delete the record
        result = record.delete()
        assert result == True

        # Load records and check deletion
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 0

        # Add email column to table object
        email_column = SQLiteColumn(
            id=3,
            name='email',
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=True,
            check="email LIKE '%@%'"
        )

        # Add email column using column.add()
        result = email_column.add()
        assert result == True

        table.columns._value.append(email_column)

        # Insert a new record with valid email
        new_record2 = SQLiteRecord(
            id=-1,
            table=table,
            values={'name': 'Alice', 'email': 'alice@example.com'}
        )
        result = new_record2.insert()
        assert result == True

        # Load records and check
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values['name'] == 'Alice'
        assert records[0].values['email'] == 'alice@example.com'

        # Try to insert a record with invalid email (should fail due to CHECK)
        new_record3 = SQLiteRecord(
            id=-1,
            table=table,
            values={'name': 'Bob', 'email': 'invalidemail'}
        )
        result = new_record3.insert()
        assert result == False  # Should fail due to CHECK constraint

        # Truncate the table (empty and reset auto increment)
        result = table.truncate()
        assert result == True

        # Load records and check truncation
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 0

        # Insert another record to check auto increment reset
        new_record4 = SQLiteRecord(
            id=-1,
            table=table,
            values={'name': 'Charlie', 'email': 'charlie@test.com'}
        )
        result = new_record4.insert()
        assert result == True

        # Load and check id is 1 (reset)
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values['name'] == 'Charlie'
        assert records[0].values['id'] == 1  # Auto increment reset

        # Drop the table
        result = table.drop()
        assert result == True

        # Verify table was dropped
        result = session.context.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        row = session.context.fetchone()
        assert row is None
