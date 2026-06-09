import pytest


class BaseViewCreateDropTests:

    def test_view_create(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_create_view",
            statement=self.get_simple_view_statement(),
        )
        assert view.is_new is True

        result = view.create()
        assert result is True

        database.views.refresh()
        assert any(v.name == "test_create_view" for v in database.views.get_value())

        view.drop()

    def test_view_drop(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_drop_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()
        database.views.refresh()

        created = next((v for v in database.views.get_value() if v.name == "test_drop_view"), None)
        assert created is not None

        result = created.drop()
        assert result is True

        database.views.refresh()
        assert not any(v.name == "test_drop_view" for v in database.views.get_value())

    def test_view_list_via_database_observable(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_list_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()
        database.views.refresh()

        views = database.views.get_value()
        assert any(v.name == "test_list_view" for v in views)

        view.drop()

    def test_view_list_has_name_and_statement(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_fields_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()
        database.views.refresh()

        found = next((v for v in database.views.get_value() if v.name == "test_fields_view"), None)
        assert found is not None
        assert found.name == "test_fields_view"
        assert found.statement

        found.drop()

    def get_simple_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_simple_view_statement()")


class BaseViewAlterTests:

    def test_view_alter_changes_statement(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_alter_direct_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()
        database.views.refresh()

        created = next((v for v in database.views.get_value() if v.name == "test_alter_direct_view"), None)
        assert created is not None

        created.statement = self.get_updated_view_statement()
        result = created.alter()
        assert result is True

        database.views.refresh()
        updated = next((v for v in database.views.get_value() if v.name == "test_alter_direct_view"), None)
        assert updated is not None

        created.drop()

    def get_simple_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_simple_view_statement()")

    def get_updated_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_updated_view_statement()")


class BaseViewSaveTests:

    def test_save_creates_new_view_and_refreshes_database(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_save_view",
            statement=self.get_view_statement(),
        )

        assert view.is_new is True

        result = view.save()

        assert result is True
        database.views.refresh()
        views = database.views.get_value()
        assert any(v.name == "test_save_view" for v in views)

        view.drop()

    def test_save_alters_existing_view_and_refreshes_database(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_alter_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()

        database.views.refresh()
        views = database.views.get_value()
        created_view = next((v for v in views if v.name == "test_alter_view"), None)
        assert created_view is not None

        created_view.statement = self.get_updated_view_statement()

        result = created_view.save()

        assert result is True
        database.views.refresh()
        views = database.views.get_value()
        updated_view = next((v for v in views if v.name == "test_alter_view"), None)
        assert updated_view is not None

        created_view.drop()

    def get_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_view_statement()")

    def get_simple_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_simple_view_statement()")

    def get_updated_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_updated_view_statement()")


class BaseViewIsNewTests:

    def test_is_new_returns_true_for_new_view(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="new_view",
            statement=self.get_simple_view_statement(),
        )

        assert view.is_new is True

    def test_is_new_returns_false_for_existing_view(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="existing_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()

        database.views.refresh()
        views = database.views.get_value()
        existing_view = next((v for v in views if v.name == "existing_view"), None)

        assert existing_view is not None
        assert existing_view.is_new is False

        existing_view.drop()

    def get_simple_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_simple_view_statement()")


class BaseViewColumnsTests:

    def test_view_columns_are_loadable(self, session, database, create_users_table):
        create_users_table(database, session)
        view = session.context.build_empty_view(
            database,
            name="test_cols_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_cols_view")
        columns = list(view.columns)

        assert len(columns) > 0

        view.drop()

    def test_view_columns_have_name_attribute(self, session, database, create_users_table):
        create_users_table(database, session)
        view = session.context.build_empty_view(
            database,
            name="test_colnames_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_colnames_view")
        columns = list(view.columns)

        assert all(hasattr(c, "name") and c.name for c in columns)

        view.drop()

    def test_view_columns_include_expected_names(self, session, database, create_users_table):
        create_users_table(database, session)
        view = session.context.build_empty_view(
            database,
            name="test_expected_cols_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_expected_cols_view")
        column_names = [c.name for c in view.columns]

        assert "name" in column_names

        view.drop()

    def test_view_columns_have_datatype(self, session, database, create_users_table):
        create_users_table(database, session)
        view = session.context.build_empty_view(
            database,
            name="test_datatype_cols_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_datatype_cols_view")
        columns = list(view.columns)

        assert all(hasattr(c, "datatype") and c.datatype is not None for c in columns)

        view.drop()

    def get_users_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_users_view_statement()")


class BaseViewRecordsTests:

    def test_view_load_records_empty_when_table_empty(self, session, database, create_users_table):
        create_users_table(database, session)
        view = session.context.build_empty_view(
            database,
            name="test_empty_records_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_empty_records_view")
        view.load_records()

        assert len(list(view.records)) == 0

        view.drop()

    def test_view_load_records_with_data(self, session, database, create_users_table):
        table = create_users_table(database, session)
        record = session.context.build_empty_record(table, values={"name": "Alice"})
        record.insert()

        view = session.context.build_empty_view(
            database,
            name="test_data_records_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_data_records_view")
        view.load_records()
        records = list(view.records)

        assert len(records) == 1
        assert records[0].values.get("name") == "Alice"

        view.drop()

    def test_view_load_records_reflects_table_data(self, session, database, create_users_table):
        table = create_users_table(database, session)
        for name in ["Alice", "Bob", "Charlie"]:
            session.context.build_empty_record(table, values={"name": name}).insert()

        view = session.context.build_empty_view(
            database,
            name="test_multi_records_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_multi_records_view")
        view.load_records()

        assert len(list(view.records)) == 3

        view.drop()

    def test_view_load_records_with_limit(self, session, database, create_users_table):
        table = create_users_table(database, session)
        for name in ["Alice", "Bob", "Charlie"]:
            session.context.build_empty_record(table, values={"name": name}).insert()

        view = session.context.build_empty_view(
            database,
            name="test_limit_records_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_limit_records_view")
        view.load_records(limit=2)

        assert len(list(view.records)) == 2

        view.drop()

    def test_view_load_records_with_offset(self, session, database, create_users_table):
        table = create_users_table(database, session)
        for name in ["Alice", "Bob", "Charlie"]:
            session.context.build_empty_record(table, values={"name": name}).insert()

        view = session.context.build_empty_view(
            database,
            name="test_offset_records_view",
            statement=self.get_users_view_statement(),
        )
        view.create()
        database.views.refresh()

        view = next(v for v in database.views.get_value() if v.name == "test_offset_records_view")
        view.load_records(limit=10, offset=2)

        assert len(list(view.records)) == 1

        view.drop()

    def get_users_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_users_view_statement()")


class BaseViewCopyTests:

    def test_view_copy_creates_independent_instance(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="original_view",
            statement=self.get_simple_view_statement(),
        )

        copy = view.copy()

        assert copy is not view
        assert copy.name == view.name
        assert copy.statement == view.statement

    def test_view_copy_shares_database_reference(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="db_ref_view",
            statement=self.get_simple_view_statement(),
        )

        copy = view.copy()

        assert copy.database is view.database

    def test_view_copy_preserves_handlers(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="handlers_view",
            statement=self.get_simple_view_statement(),
        )

        copy = view.copy()

        assert copy.get_columns_handler == view.get_columns_handler
        assert copy.get_records_handler == view.get_records_handler

    def test_view_copy_has_independent_columns_observable(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="lazy_cols_view",
            statement=self.get_simple_view_statement(),
        )

        copy = view.copy()

        assert copy.columns is not view.columns

    def test_view_copy_is_new_matches_original(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="is_new_copy_view",
            statement=self.get_simple_view_statement(),
        )
        assert view.is_new is True

        copy = view.copy()
        assert copy.is_new is True

    def get_simple_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_simple_view_statement()")


class BaseViewDefinerTests:

    def test_get_definers_returns_list(self, session):
        definers = session.context.get_definers()

        assert isinstance(definers, list)
        assert len(definers) > 0
        assert all('@' in definer for definer in definers)