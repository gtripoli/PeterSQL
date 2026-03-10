import uuid


class BaseDatabaseCreateAlterTests:

    def _build_new_database(self, database, session, name: str):
        database_class = database.__class__
        new_database = database_class(id=-1, name=name, context=session.context)

        for key, value in self.get_create_options().items():
            if hasattr(new_database, key):
                setattr(new_database, key, value)

        return new_database

    @staticmethod
    def _find_database_by_name(session, name: str):
        session.context.databases.refresh()
        return next((db for db in session.context.databases.get_value() if db.name == name), None)

    def _execute_database_operation(self, session, operation):
        if not self.requires_autocommit_for_database_ddl():
            operation()
            return

        connection = getattr(session.context, "_connection", None)
        if connection is None or not hasattr(connection, "autocommit"):
            operation()
            return

        connection.commit()

        previous_autocommit = connection.autocommit
        connection.autocommit = True
        try:
            operation()
        finally:
            connection.autocommit = previous_autocommit

    def _drop_database(self, session, database) -> bool:
        result = False

        def operation() -> None:
            nonlocal result
            result = database.drop()

        self._execute_database_operation(session, operation)
        return result

    def _create_database(self, database) -> bool:
        if not self.requires_autocommit_for_database_ddl():
            return database.create()

        connection = getattr(database.context, "_connection", None)
        if connection is None or not hasattr(connection, "autocommit"):
            return database.create()

        connection.commit()

        previous_autocommit = connection.autocommit
        connection.autocommit = True
        try:
            return database.create()
        finally:
            connection.autocommit = previous_autocommit

    @staticmethod
    def _build_unique_database_name() -> str:
        unique_name = str(uuid.uuid4()).replace("-", "")[:12]
        return f"db_{unique_name}"

    def test_database_create_and_drop(self, session, database):
        name = self._build_unique_database_name()
        created_database = self._build_new_database(database, session, name)

        assert self._create_database(created_database) is True

        loaded_database = self._find_database_by_name(session, name)
        assert loaded_database is not None

        assert self._drop_database(session, loaded_database) is True

    def test_database_alter(self, database):
        for key, value in self.get_alter_options().items():
            if hasattr(database, key):
                setattr(database, key, value)

        assert database.alter() is True

    def get_create_options(self) -> dict[str, str]:
        return {}

    def get_alter_options(self) -> dict[str, str]:
        return {}

    def requires_autocommit_for_database_ddl(self) -> bool:
        return False


class BaseDatabaseUnsupportedTests:

    @staticmethod
    def _build_new_database(database, session, name: str):
        database_class = database.__class__
        return database_class(id=-1, name=name, context=session.context)

    @staticmethod
    def _build_unique_database_name() -> str:
        unique_name = str(uuid.uuid4()).replace("-", "")[:12]
        return f"db_{unique_name}"

    def test_database_create_returns_false(self, session, database):
        name = self._build_unique_database_name()
        new_database = self._build_new_database(database, session, name)

        assert new_database.create() is False

    def test_database_alter_returns_false(self, database):
        assert database.alter() is False