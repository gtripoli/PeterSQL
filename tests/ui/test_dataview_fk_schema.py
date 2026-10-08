import wx

from constants import WORKDIR
from helpers.observables import ObservableLazyList
from icons import IconRegistry
from structures.connection import Connection, ConnectionEngine, SourceConfiguration
from structures.engines.context import AbstractContext
from structures.engines.database import SQLColumn, SQLRecord, SQLTable
from structures.engines.datatype import StandardDataType
from structures.engines.postgresql.database import PostgreSQLDatabase, PostgreSQLTable, PostgreSQLForeignKey
from structures.session import Session, SessionState
from tests.ui.scenario_helpers import pump_ui
from windows.components.dataview import TableForeignKeysDataViewCtrl
from windows.components.popup import PopupChoice
from windows.state import CURRENT_DATABASE, CURRENT_SESSION, CURRENT_TABLE


class MockPostgreSQLContext(AbstractContext):
    def __init__(self, connection):
        self.connection = connection
        self.databases = ObservableLazyList(lambda: [])
        self.records_by_table = {}

    def connect(self, **connect_kwargs):
        pass

    def set_database(self, database):
        pass

    def get_server_version(self):
        return ""

    def get_server_uptime(self):
        return None

    def get_databases(self):
        return self.databases.get_value()

    def get_views(self, database):
        return []

    def get_triggers(self, database):
        return []

    def get_tables(self, database):
        return database.tables.get_value()

    def get_columns(self, table):
        return table.columns.get_value()

    def get_indexes(self, table):
        return table.indexes.get_value()

    def get_foreign_keys(self, table):
        return table.foreign_keys.get_value()

    def build_empty_database(self, name=""):
        return PostgreSQLDatabase(id=-1, name=name, context=self)

    def build_empty_table(self, database, name=None, **default_values):
        return PostgreSQLTable(id=-1, name=name or "", database=database, **default_values)

    def build_empty_column(self, table, datatype, name=None, **default_values):
        return SQLColumn(id=-1, name=name or "", table=table, datatype=datatype, **default_values)

    def build_empty_index(self, table, indextype, columns, name=None, **default_values):
        return None

    def build_empty_check(self, table, name=None, expression=None, **default_values):
        return None

    def build_empty_foreign_key(self, table, columns, name=None, **default_values):
        return PostgreSQLForeignKey(
            id=-1,
            name=name or "",
            table=table,
            columns=columns,
            reference_table=default_values.get("reference_table", ""),
            reference_columns=default_values.get("reference_columns", []),
        )

    def build_empty_record(self, table, *, values):
        return SQLRecord(id=-1, table=table, values=values)

    def build_empty_view(self, database, name=None, **default_values):
        return None

    def build_empty_function(self, database, name=None, **default_values):
        return None

    def build_empty_procedure(self, database, name=None, **default_values):
        return None

    def build_empty_trigger(self, database, name=None, **default_values):
        return None

    def get_result_column_datatypes(self, cursor):
        return []

    def get_records(self, table, /, *, filters=None, limit=1000, offset=0, orders=None):
        return self.records_by_table.get(table.name, [])


def _create_schema_session(monkeypatch):
    monkeypatch.setattr(Session, "_get_context_class", lambda self: MockPostgreSQLContext)

    connection = Connection(
        id=1,
        name="schema-qualified-fk-session",
        engine=ConnectionEngine.POSTGRESQL,
        configuration=SourceConfiguration(filename=":memory:"),
    )
    session = Session(connection)
    session.set_state(SessionState.CONNECTED)

    database = PostgreSQLDatabase(id=1, name="test_db", context=session.context)
    skill_table = PostgreSQLTable(id=1, name="skill", schema="public", database=database)
    employee_table = PostgreSQLTable(id=2, name="employee", schema="public", database=database)

    skill_id_column = SQLColumn(
        id=1,
        name="id",
        table=skill_table,
        datatype=StandardDataType.INTEGER,
    )
    employee_skill_id_column = SQLColumn(
        id=1,
        name="skill_id",
        table=employee_table,
        datatype=StandardDataType.INTEGER,
    )
    foreign_key = PostgreSQLForeignKey(
        id=1,
        name="fk_employee_skill",
        table=employee_table,
        columns=["skill_id"],
        reference_table="public.skill",
        reference_columns=["id"],
    )

    skill_table.columns.set_value([skill_id_column])
    employee_table.columns.set_value([employee_skill_id_column])
    employee_table.foreign_keys.set_value([foreign_key])
    database.tables.set_value([skill_table])
    session.context.databases.set_value([database])

    return session, database, employee_table, foreign_key


def _popup_choice_values(popup):
    return [popup.choice.GetString(index) for index in range(popup.choice.GetCount())]


def test_fk_reference_table_dropdown_uses_schema_qualified_name(monkeypatch, wx_app):
    session, database, employee_table, foreign_key = _create_schema_session(monkeypatch)

    app = wx.GetApp()
    app.icon_registry_16 = IconRegistry(str(WORKDIR / "icons"), 16)

    frame = wx.Frame(None, title="Schema-qualified FK test")
    dataview = TableForeignKeysDataViewCtrl(frame)

    CURRENT_SESSION.set_value(session)
    CURRENT_DATABASE.set_value(database)
    CURRENT_TABLE.set_value(employee_table)

    try:
        frame.Show()
        pump_ui(10)

        reference_table_column = dataview.GetColumn(2)
        reference_table_renderer = reference_table_column.GetRenderer()
        reference_table_popup = PopupChoice(dataview)
        reference_table_renderer.on_open(reference_table_popup)
        reference_table_popup.popup_size = wx.Size(200, -1)
        reference_table_popup.open("", wx.DefaultPosition)
        pump_ui(5)

        assert _popup_choice_values(reference_table_popup) == ["public.skill"]

        reference_table_renderer.SetValue("public.skill")
        pump_ui(5)

        reference_columns_column = dataview.GetColumn(3)
        reference_columns_renderer = reference_columns_column.GetRenderer()
        reference_columns_popup = PopupChoice(dataview)
        reference_columns_renderer.on_open(reference_columns_popup)
        reference_columns_popup.popup_size = wx.Size(200, -1)
        reference_columns_popup.open("", wx.DefaultPosition)
        pump_ui(5)

        assert _popup_choice_values(reference_columns_popup) == ["id"]
    finally:
        frame.Destroy()
        CURRENT_TABLE.set_value(None)
        CURRENT_DATABASE.set_value(None)
        CURRENT_SESSION.set_value(None)
        pump_ui(5)
