import datetime
import decimal
import json
import pathlib

from typing import Any


def create_database_dump(
    database: Any,
    /,
    *,
    include_schema: bool = True,
    include_records: bool = True,
) -> str:
    database.context.set_database(database)
    dump_path = _build_dump_path(database.name)
    with dump_path.open("w", encoding="utf-8") as handle:
        _write_header(handle)
        if include_schema:
            _write_schema(handle, database)
        if include_records:
            _write_records(handle, database)

    return str(dump_path)


def _build_dump_path(database_name: str) -> pathlib.Path:
    now = datetime.datetime.now()
    safe_name = "".join(char if char.isalnum() or char == "_" else "_" for char in database_name)
    suffix = now.strftime("%Y%m%d_%H%M%S_%f")
    filename = f"petersql_backup_{safe_name}_{suffix}.sql"
    return pathlib.Path.cwd() / filename


def _write_header(handle):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    handle.write(f"-- This backup was created by PeterSQL on {now}\n\n")


def _write_records(handle, database: Any):
    _write_section_title(handle, "Insert records")
    statements = _collect_record_statements(database)
    _write_statements(handle, statements)


def _write_schema(handle, database: Any):
    _write_section_title(handle, "Create database")
    _write_statements(handle, _collect_database_statements(database))

    _write_section_title(handle, "Create tables")
    _write_statements(handle, _collect_table_statements(database))

    _write_section_title(handle, "Create indexes/triggers/views/procedures/functions")
    _write_statements(handle, _collect_secondary_statements(database))


def _write_section_title(handle, title: str):
    handle.write(f"-- {title}\n")
    handle.write("-- ----------------------------------------\n")


def _write_statements(handle, statements: list[str]):
    if not statements:
        handle.write("-- No statements\n\n")
        return

    for statement in statements:
        if not statement:
            continue
        handle.write(statement.rstrip())
        handle.write("\n\n")


def _collect_database_statements(database: Any) -> list[str]:
    context = database.context
    context_name = context.__class__.__name__.lower()
    if "sqlite" in context_name:
        return ["-- SQLite does not support CREATE DATABASE statements"]

    database_name = context.quote_identifier(database.name)
    create_statement = f"CREATE DATABASE {database_name};"
    if "postgresql" in context_name:
        return [create_statement, f"\\connect {database.name}"]

    return [create_statement, f"USE {database_name};"]


def _collect_table_statements(database: Any) -> list[str]:
    statements = []
    tables = sorted(list(database.tables), key=lambda table: table.name)
    for table in tables:
        statements.append(_normalize_statement(table.raw_create()))

    return [statement for statement in statements if statement]


def _collect_secondary_statements(database: Any) -> list[str]:
    statements = []
    statements.extend(_collect_index_statements(database))
    statements.extend(_collect_trigger_statements(database))
    statements.extend(_collect_view_statements(database))
    statements.extend(_collect_procedure_statements(database))
    statements.extend(_collect_function_statements(database))
    return [statement for statement in statements if statement]


def _collect_index_statements(database: Any) -> list[str]:
    statements = []
    context_name = database.context.__class__.__name__.lower()
    tables = sorted(list(database.tables), key=lambda table: table.name)
    for table in tables:
        indexes = sorted(list(table.indexes), key=lambda index: index.name)
        for index in indexes:
            if not _is_dumpable_index(index, context_name):
                continue

            statements.append(_normalize_statement(index.raw_create()))

    return [statement for statement in statements if statement]


def _collect_record_statements(database: Any) -> list[str]:
    statements = []
    tables = sorted(list(database.tables), key=lambda table: table.name)
    for table in tables:
        statements.extend(_table_record_statements(table))

    return statements


def _collect_trigger_statements(database: Any) -> list[str]:
    context_name = database.context.__class__.__name__.lower()
    triggers = sorted(list(getattr(database, "triggers", [])), key=lambda trigger: trigger.name)
    if "mysql" in context_name or "mariadb" in context_name:
        return [_mysql_block_statement(trigger.raw_create()) for trigger in triggers]

    return [_normalize_statement(trigger.raw_create()) for trigger in triggers]


def _collect_view_statements(database: Any) -> list[str]:
    views = sorted(list(getattr(database, "views", [])), key=lambda view: view.name)
    return [_normalize_statement(view.raw_create()) for view in views]


def _collect_function_statements(database: Any) -> list[str]:
    context_name = database.context.__class__.__name__.lower()
    functions = sorted(list(getattr(database, "functions", [])), key=lambda function: function.name)
    if "mysql" in context_name or "mariadb" in context_name:
        return [_mysql_block_statement(function.raw_create()) for function in functions]

    return [_normalize_statement(function.raw_create()) for function in functions]


def _collect_procedure_statements(database: Any) -> list[str]:
    context_name = database.context.__class__.__name__.lower()
    procedures = sorted(list(getattr(database, "procedures", [])), key=lambda procedure: procedure.name)
    if "mysql" in context_name or "mariadb" in context_name:
        return [_mysql_block_statement(procedure.raw_create()) for procedure in procedures]

    return [_normalize_statement(procedure.raw_create()) for procedure in procedures]


def _is_dumpable_index(index: Any, context_name: str) -> bool:
    if index.type.name == "PRIMARY":
        return False

    if "sqlite" in context_name and index.name.startswith("sqlite_autoindex_"):
        return False

    return True


def _mysql_block_statement(statement: str) -> str:
    statement = statement.strip().rstrip(";")
    return f"DELIMITER $$\n{statement}$$\nDELIMITER ;"


def _normalize_statement(statement: str) -> str:
    statement = statement.strip().rstrip(";")
    if not statement:
        return ""
    return f"{statement};"


def _render_literal(value: Any, table: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return _render_boolean(value, table)
    if isinstance(value, (int, float, decimal.Decimal)):
        return str(value)
    if isinstance(value, datetime.datetime):
        return _quote_literal(value.isoformat(sep=" "))
    if isinstance(value, (datetime.date, datetime.time)):
        return _quote_literal(value.isoformat())
    if isinstance(value, (bytes, bytearray, memoryview)):
        return _quote_literal(bytes(value).hex())
    if isinstance(value, (dict, list, tuple, set)):
        return _quote_literal(json.dumps(value, ensure_ascii=False))

    return _quote_literal(str(value))


def _render_boolean(value: bool, table: Any) -> str:
    context_name = table.database.context.__class__.__name__.lower()
    if "postgresql" in context_name:
        return "TRUE" if value else "FALSE"
    return "1" if value else "0"


def _table_record_statements(table: Any) -> list[str]:
    context = table.database.context
    columns = [column for column in table.columns if getattr(column, "virtuality", None) is None]
    if not columns:
        return []

    table_name = _table_reference(table)
    column_names = ", ".join(context.quote_identifier(column.name) for column in columns)
    ordering = ", ".join(context.quote_identifier(column.name) for column in columns)
    return _table_record_pages(table, table_name, column_names, columns, ordering)


def _table_record_pages(
    table: Any,
    table_name: str,
    column_names: str,
    columns: list[Any],
    ordering: str,
) -> list[str]:
    offset = 0
    limit = 1000
    statements = []
    while True:
        records = table.database.context.get_records(table, limit=limit, offset=offset, orders=ordering)
        if not records:
            break

        statements.extend(_table_record_page(table, table_name, column_names, columns, records))
        if len(records) < limit:
            break

        offset += limit

    return statements


def _table_record_page(
    table: Any,
    table_name: str,
    column_names: str,
    columns: list[Any],
    records: list[Any],
) -> list[str]:
    statements = []
    for record in records:
        values = [_render_literal(record.values.get(column.name), table) for column in columns]
        values_sql = ", ".join(values)
        statements.append(f"INSERT INTO {table_name} ({column_names}) VALUES ({values_sql});")

    return statements


def _table_reference(table: Any) -> str:
    context = table.database.context
    context_name = context.__class__.__name__.lower()
    if "sqlite" in context_name:
        return context.quote_identifier(table.name)

    return table.fully_qualified_name


def _quote_literal(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"