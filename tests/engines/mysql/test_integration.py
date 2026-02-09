import pytest

from structures.engines.mysql.database import (
    MySQLTable,
    MySQLColumn,
    MySQLIndex,
    MySQLForeignKey,
    MySQLRecord,
    MySQLView,
    MySQLTrigger,
    MySQLFunction,
)
from structures.engines.mysql.datatype import MySQLDataType
from structures.engines.mysql.indextype import MySQLIndexType


class TestMySQLIntegration:
    """
    Integration tests for MySQL engine.
    Tests the complete workflow in a single test to reuse the container.
    """

    def test_complete_workflow(self, mysql_database, mysql_session):
        """
        Test complete MySQL workflow:
        table -> columns -> indexes -> foreign keys -> triggers -> views -> functions
        """
        ctx = mysql_session.context
        ctx.execute("USE testdb")

        # === TABLE CREATION ===
        users_table = MySQLTable(
            id=1,
            name="users",
            database=mysql_database,
            engine="InnoDB",
            collation_name="utf8_general_ci",
        )

        col_id = MySQLColumn(
            id=1,
            name="id",
            table=users_table,
            datatype=MySQLDataType.INT,
            is_nullable=False,
            is_auto_increment=True,
            length=11,
        )
        col_name = MySQLColumn(
            id=2,
            name="name",
            table=users_table,
            datatype=MySQLDataType.VARCHAR,
            length=255,
        )
        col_email = MySQLColumn(
            id=3,
            name="email",
            table=users_table,
            datatype=MySQLDataType.VARCHAR,
            length=255,
        )
        users_table.columns.set_value([col_id, col_name, col_email])

        primary_index = MySQLIndex(
            id=1,
            name="PRIMARY",
            type=MySQLIndexType.PRIMARY,
            columns=["id"],
            table=users_table,
        )
        users_table.indexes.set_value([primary_index])

        ctx.execute(users_table.raw_create())

        ctx.execute("USE testdb")
        ctx.execute("SHOW TABLES LIKE 'users'")
        assert ctx.fetchone() is not None

        # === COLUMN ADD ===
        col_created = MySQLColumn(
            id=4,
            name="created_at",
            table=users_table,
            datatype=MySQLDataType.DATETIME,
            is_nullable=True,
        )
        col_created.add()

        ctx.execute("DESCRIBE users")
        columns = ctx.fetchall()
        assert len(columns) == 4
        assert columns[3]["Field"] == "created_at"

        # === INDEX CREATE/DROP ===
        idx_email = MySQLIndex(
            id=2,
            name="idx_email",
            type=MySQLIndexType.UNIQUE,
            columns=["email"],
            table=users_table,
        )
        assert idx_email.create() is True

        ctx.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_email'")
        assert ctx.fetchone() is not None

        assert idx_email.drop() is True

        ctx.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_email'")
        assert ctx.fetchone() is None

        # === FOREIGN KEY ===
        orders_table = MySQLTable(
            id=2,
            name="orders",
            database=mysql_database,
            engine="InnoDB",
            collation_name="utf8_general_ci",
        )

        ord_col_id = MySQLColumn(
            id=1,
            name="id",
            table=orders_table,
            datatype=MySQLDataType.INT,
            is_nullable=False,
            is_auto_increment=True,
            length=11,
        )
        ord_col_user_id = MySQLColumn(
            id=2,
            name="user_id",
            table=orders_table,
            datatype=MySQLDataType.INT,
            is_nullable=True,
            length=11,
        )
        ord_col_total = MySQLColumn(
            id=3,
            name="total",
            table=orders_table,
            datatype=MySQLDataType.DECIMAL,
            length=10,
        )
        orders_table.columns.set_value([ord_col_id, ord_col_user_id, ord_col_total])
        orders_table.indexes.set_value([
            MySQLIndex(id=1, name="PRIMARY", type=MySQLIndexType.PRIMARY, columns=["id"], table=orders_table),
        ])
        ctx.execute(orders_table.raw_create())

        fk = MySQLForeignKey(
            id=1,
            name="fk_orders_users",
            table=orders_table,
            columns=["user_id"],
            reference_table="users",
            reference_columns=["id"],
            on_update="CASCADE",
            on_delete="SET NULL",
        )
        assert fk.create() is True

        ctx.execute("""
            SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
            WHERE TABLE_NAME = 'orders' AND CONSTRAINT_TYPE = 'FOREIGN KEY'
        """)
        assert ctx.fetchone()["CONSTRAINT_NAME"] == "fk_orders_users"

        # === VIEW ===
        view = MySQLView(
            id=1,
            name="active_users_view",
            database=mysql_database,
            sql="SELECT * FROM testdb.users WHERE name IS NOT NULL",
        )
        assert view.create() is True

        ctx.execute("""
            SELECT TABLE_NAME FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = 'testdb' AND TABLE_NAME = 'active_users_view'
        """)
        assert ctx.fetchone() is not None

        assert view.drop() is True

        ctx.execute("""
            SELECT TABLE_NAME FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = 'testdb' AND TABLE_NAME = 'active_users_view'
        """)
        assert ctx.fetchone() is None

        # === TRIGGER ===
        trigger = MySQLTrigger(
            id=1,
            name="trg_users_update",
            database=mysql_database,
            sql="BEFORE UPDATE ON testdb.users FOR EACH ROW SET NEW.created_at = NOW()",
            timing="BEFORE",
            event="UPDATE",
        )
        assert trigger.create() is True

        ctx.execute("""
            SELECT TRIGGER_NAME FROM information_schema.TRIGGERS
            WHERE TRIGGER_SCHEMA = 'testdb' AND TRIGGER_NAME = 'trg_users_update'
        """)
        assert ctx.fetchone() is not None

        assert trigger.drop() is True

        ctx.execute("""
            SELECT TRIGGER_NAME FROM information_schema.TRIGGERS
            WHERE TRIGGER_SCHEMA = 'testdb' AND TRIGGER_NAME = 'trg_users_update'
        """)
        assert ctx.fetchone() is None

        # === FUNCTION ===
        function = MySQLFunction(
            id=1,
            name="calc_total",
            database=mysql_database,
            parameters="price DECIMAL(10,2), quantity INT",
            returns="DECIMAL(10,2)",
            deterministic=True,
            sql="RETURN price * quantity",
        )
        assert function.create() is True

        ctx.execute("""
            SELECT ROUTINE_NAME FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = 'testdb' AND ROUTINE_NAME = 'calc_total'
        """)
        assert ctx.fetchone() is not None

        ctx.execute("SELECT testdb.calc_total(10.50, 3) AS result")
        assert float(ctx.fetchone()["result"]) == 31.50

        assert function.drop() is True

        # === RECORD INSERT ===
        record = MySQLRecord(
            id=1,
            table=orders_table,
            values={"total": "100.00"},
        )
        assert record.insert() is True

        ctx.execute("SELECT COUNT(*) as cnt FROM orders")
        assert ctx.fetchone()["cnt"] == 1

        # === TRUNCATE (on orders table, not referenced by FK) ===
        orders_table.truncate()

        ctx.execute("SELECT COUNT(*) as cnt FROM orders")
        assert ctx.fetchone()["cnt"] == 0

        # === CLEANUP ===
        orders_table.drop()
        users_table.drop()

        ctx.execute("SHOW TABLES LIKE 'users'")
        assert ctx.fetchone() is None

        ctx.execute("SHOW TABLES LIKE 'orders'")
        assert ctx.fetchone() is None
