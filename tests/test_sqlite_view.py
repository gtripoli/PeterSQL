import pytest
from unittest.mock import patch

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteView


class TestSQLiteView:
    @pytest.fixture
    def database(self, sqlite_session):
        db = SQLiteDatabase(id=1, name='main', context=sqlite_session.context)
        return db

    def test_view_creation(self, database):
        view = SQLiteView(
            id=1,
            name='user_view',
            database=database,
            sql='SELECT * FROM users'
        )
        assert view.id == 1
        assert view.name == 'user_view'
        assert view.database.name == database.name
        assert view.sql == 'SELECT * FROM users'

    def test_view_copy(self, database):
        view = SQLiteView(
            id=1,
            name='user_view',
            database=database,
            sql='SELECT * FROM users'
        )
        copied_view = view.copy()
        assert copied_view.id == view.id
        assert copied_view.name == view.name
        assert copied_view.sql == view.sql
        assert copied_view is not view

    def test_view_create(self, database):
        view = SQLiteView(
            id=1,
            name='user_view',
            database=database,
            sql='SELECT * FROM users'
        )

        with patch.object(database.context, 'execute', return_value=True) as mock_execute:
            result = view.create()
            assert result == True
            mock_execute.assert_called_once_with("CREATE VIEW IF NOT EXISTS user_view AS SELECT * FROM users")

    def test_view_drop(self, database):
        view = SQLiteView(
            id=1,
            name='user_view',
            database=database,
            sql='SELECT * FROM users'
        )

        with patch.object(database.context, 'execute', return_value=True) as mock_execute:
            result = view.drop()
            assert result == True
            mock_execute.assert_called_once_with("DROP VIEW IF EXISTS user_view")

    def test_view_alter(self, database):
        view = SQLiteView(
            id=1,
            name='user_view',
            database=database,
            sql='SELECT * FROM users'
        )

        # alter does nothing
        view.alter()  # Should not raise
