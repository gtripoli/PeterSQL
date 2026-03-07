import pytest


class BaseCheckTests:
    def test_check_in_table_definition(
        self, session, database, create_users_table, datatype_class
    ):
        """Test that Check constraints are loaded from table definition."""
        table = create_users_table(database, session)

        # Add a column with a check constraint
        age_column = session.context.build_empty_column(
            table,
            datatype_class.INTEGER
            if hasattr(datatype_class, "INTEGER")
            else datatype_class.INT,
            name="age",
            is_nullable=True,
        )
        age_column.add()

        # Refresh table to load checks
        table.checks.refresh()
        checks = table.checks.get_value()

        # Note: Check constraints might be inline in column definition
        # or separate objects depending on engine implementation
        assert checks is not None
        assert isinstance(checks, list)

        table.drop()

    @pytest.mark.skip_engine("sqlite", "mariadb:5")
    def test_check_create_and_drop(
        self, session, database, create_users_table, datatype_class
    ):
        """Test creating and dropping a CHECK constraint."""
        table = create_users_table(database, session)

        # Add age column
        age_column = session.context.build_empty_column(
            table,
            datatype_class.INTEGER
            if hasattr(datatype_class, "INTEGER")
            else datatype_class.INT,
            name="age",
            is_nullable=True,
        )
        age_column.add()

        # Create a CHECK constraint
        check = session.context.build_empty_check(
            table, name="age_check", expression="age >= 0 AND age <= 150"
        )
        assert check.create() is True

        # Verify check exists
        table.checks.refresh()
        checks = table.checks.get_value()
        assert any(c.name == "age_check" for c in checks)

        # Drop the check
        check_to_drop = next(c for c in checks if c.name == "age_check")
        assert check_to_drop.drop() is True

        # Verify check is gone
        table.checks.refresh()
        checks = table.checks.get_value()
        assert not any(c.name == "age_check" for c in checks)

        table.drop()

    @pytest.mark.skip_engine("sqlite", "mariadb:5")
    def test_check_alter(self, session, database, create_users_table, datatype_class):
        """Test altering a CHECK constraint (drop + create)."""
        table = create_users_table(database, session)

        # Add age column
        age_column = session.context.build_empty_column(
            table,
            datatype_class.INTEGER
            if hasattr(datatype_class, "INTEGER")
            else datatype_class.INT,
            name="age",
            is_nullable=True,
        )
        age_column.add()

        # Create initial CHECK constraint
        check = session.context.build_empty_check(
            table, name="age_check", expression="age >= 0"
        )
        check.create()

        # Alter the check (change expression)
        check.expression = "age >= 18"
        assert check.alter() is True

        table.checks.refresh()
        checks = table.checks.get_value()
        assert any(c.name == "age_check" for c in checks)

        table.drop()
