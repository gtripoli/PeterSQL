import pytest
from unittest.mock import patch

from structures.session import Connection
from structures.engines import ConnectionEngine
from structures.configurations import SourceConfiguration
from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTrigger


class TestSQLiteTrigger:
    @pytest.fixture
    def database(self, sqlite_session):
        db = SQLiteDatabase(id=1, name='main', context=sqlite_session.context)
        return db

    def test_trigger_creation(self, database):
        trigger = SQLiteTrigger(
            id=1,
            name='after_insert_users',
            database=database,
            sql='AFTER INSERT ON users BEGIN UPDATE users SET updated_at = datetime(\'now\') WHERE id = NEW.id; END;',
            timing='AFTER',
            event='INSERT'
        )
        assert trigger.id == 1
        assert trigger.name == 'after_insert_users'
        assert trigger.database.name == database.name
        assert trigger.timing == 'AFTER'
        assert trigger.event == 'INSERT'

    def test_trigger_copy(self, database):
        trigger = SQLiteTrigger(
            id=1,
            name='after_insert_users',
            database=database,
            sql='AFTER INSERT ON users BEGIN UPDATE users SET updated_at = datetime(\'now\') WHERE id = NEW.id; END;',
            timing='AFTER',
            event='INSERT'
        )
        copied_trigger = trigger.copy()
        assert copied_trigger.id == trigger.id
        assert copied_trigger.name == trigger.name
        assert copied_trigger.sql == trigger.sql
        assert copied_trigger.timing == trigger.timing
        assert copied_trigger.event == trigger.event
        assert copied_trigger is not trigger

    def test_trigger_create(self, database):
        trigger = SQLiteTrigger(
            id=1,
            name='after_insert_users',
            database=database,
            sql='AFTER INSERT ON users BEGIN UPDATE users SET updated_at = datetime(\'now\') WHERE id = NEW.id; END;',
            timing='AFTER',
            event='INSERT'
        )

        with patch.object(database.context, 'execute', return_value=True) as mock_execute:
            result = trigger.create()
            assert result == True
            mock_execute.assert_called_once_with("CREATE TRIGGER IF NOT EXISTS after_insert_users AFTER INSERT ON users BEGIN UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id; END;")

    def test_trigger_drop(self, database):
        trigger = SQLiteTrigger(
            id=1,
            name='after_insert_users',
            database=database,
            sql='AFTER INSERT ON users BEGIN UPDATE users SET updated_at = datetime(\'now\') WHERE id = NEW.id; END;',
            timing='AFTER',
            event='INSERT'
        )

        with patch.object(database.context, 'execute', return_value=True) as mock_execute:
            result = trigger.drop()
            assert result == True
            mock_execute.assert_called_once_with("DROP TRIGGER IF EXISTS after_insert_users")

    def test_trigger_alter(self, database):
        trigger = SQLiteTrigger(
            id=1,
            name='after_insert_users',
            database=database,
            sql='AFTER INSERT ON users BEGIN UPDATE users SET updated_at = datetime(\'now\') WHERE id = NEW.id; END;',
            timing='AFTER',
            event='INSERT'
        )

        # alter does nothing
        trigger.alter()  # Should not raise
