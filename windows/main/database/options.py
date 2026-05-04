from typing import Optional

import wx

from helpers.bindings import AbstractModel, wx_call_after_debounce
from helpers.logger import logger
from helpers.observables import Observable, debounce

from structures.connection import ConnectionEngine

from windows.main import CURRENT_DATABASE, CURRENT_SESSION
from windows.state import NEW_DATABASE


class EditDatabaseModel(AbstractModel):
    def __init__(self):
        super().__init__()

        self.name = Observable()
        self.collation = Observable()
        self.encryption = Observable(False)
        self.tablespace = Observable()
        self.connection_limit = Observable(0)

        wx_call_after_debounce(
            self.name,
            self.collation,
            self.encryption,
            self.tablespace,
            self.connection_limit,
            callback=self.update_database,
        )

        CURRENT_DATABASE.subscribe(self._load_database)

    @staticmethod
    def _encryption_to_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().upper() in ("Y", "YES", "TRUE", "1", "ON")

    def _load_database(self, database) -> None:
        NEW_DATABASE.set_value(None)

        if database is None:
            return

        self.name.set_initial(database.name or "")
        self.collation.set_initial(getattr(database, "default_collation", None) or "")
        self.encryption.set_initial(self._encryption_to_bool(getattr(database, "encryption", None)))
        self.tablespace.set_initial(getattr(database, "tablespace", None) or "")
        self.connection_limit.set_initial(int(getattr(database, "connection_limit", None) or 0))

    def update_database(self, *args) -> None:
        if not any(args):
            return

        database = NEW_DATABASE.get_value() or CURRENT_DATABASE.get_value()
        if database is None:
            return

        session = CURRENT_SESSION.get_value()
        engine = session.engine if session else None

        new_name = self.name.get_value() or ""
        new_collation = self.collation.get_value() or None
        new_tablespace = self.tablespace.get_value() or None
        new_connection_limit = int(self.connection_limit.get_value() or 0)

        is_mysql = engine == ConnectionEngine.MYSQL
        new_encryption = ("Y" if self.encryption.get_value() else "N") if is_mysql else None

        name_changed = new_name != (database.name or "")
        collation_changed = new_collation != getattr(database, "default_collation", None)
        encryption_changed = new_encryption != getattr(database, "encryption", None)
        tablespace_changed = new_tablespace != getattr(database, "tablespace", None)
        connection_limit_changed = new_connection_limit != int(getattr(database, "connection_limit", None) or 0)

        if not any([name_changed, collation_changed, encryption_changed, tablespace_changed, connection_limit_changed]):
            return

        logger.debug(
            "ui trace: update_database db_id=%s old_name=%r new_name=%r obs_name=%r name_changed=%s",
            getattr(database, "id", None),
            getattr(database, "name", None),
            new_name,
            self.name.get_value(),
            name_changed,
        )

        if name_changed:
            if not hasattr(database, "_original_name"):
                database._original_name = database.name
            database.name = new_name
            logger.debug(
                "ui trace: update_database applied name db_id=%s name=%r",
                getattr(database, "id", None),
                database.name,
            )

        changed_fields: set[str] = getattr(database, "_changed_fields", set())

        if collation_changed and hasattr(database, "default_collation"):
            database.default_collation = new_collation
            changed_fields.add("default_collation")
            if hasattr(database, "character_set") and new_collation:
                collations = getattr(database.context, "COLLATIONS", {}) or {}
                if charset := collations.get(new_collation):
                    database.character_set = charset
                    changed_fields.add("character_set")

        if encryption_changed and hasattr(database, "encryption"):
            database.encryption = new_encryption
            changed_fields.add("encryption")

        if tablespace_changed and hasattr(database, "tablespace"):
            database.tablespace = new_tablespace
            changed_fields.add("tablespace")

        if connection_limit_changed and hasattr(database, "connection_limit"):
            database.connection_limit = new_connection_limit or None
            changed_fields.add("connection_limit")

        NEW_DATABASE.set_value(database)


class DatabaseOptionsController:
    def __init__(self, parent):
        self.parent = parent
        self.model = EditDatabaseModel()
        self._panel_by_name = self._build_panel_by_name()
        self._panels_all = list(self._panel_by_name.values())
        self._controls_all = self._build_controls_all()

        self._bind_controls()

        CURRENT_SESSION.subscribe(self._on_current_session)
        CURRENT_DATABASE.subscribe(self._on_current_database)

    def _on_current_database(self, _=None) -> None:
        wx.CallAfter(self._apply_current_state)

    def _on_current_session(self, _=None) -> None:
        wx.CallAfter(self._apply_current_state)

    def _apply_current_state(self) -> None:
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        engine = session.engine if session else None
        self._populate_choices(database, engine)
        self._apply_engine(engine)

    def _apply_choice(self, choice: wx.Choice, items: list, selected: Optional[str]) -> None:
        normalized = [str(item) for item in items if item is not None and str(item)]
        selected_str = str(selected) if selected else ""

        if selected_str and selected_str not in normalized:
            normalized.append(selected_str)

        if not normalized:
            choice.Clear()
            return

        choice.SetItems(normalized)
        if selected_str and choice.SetStringSelection(selected_str):
            return
        choice.SetSelection(0)

    def _apply_engine(self, engine: Optional[ConnectionEngine]) -> None:
        panel_names = self._get_panel_names_for_engine(engine)
        visible = {self._panel_by_name[name] for name in panel_names}
        for panel in self._panels_all:
            panel.Show(panel in visible)
        self._apply_readonly_rules(engine)
        self._layout_database_options()

    def _apply_readonly_rules(self, engine: Optional[ConnectionEngine]) -> None:
        is_sqlite = engine == ConnectionEngine.SQLITE
        database = CURRENT_DATABASE.get_value()
        is_new = database is not None and database.is_new
        name_readonly = not is_new and engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB, ConnectionEngine.SQLITE)
        self.parent.database_name.Enable(True)
        self.parent.database_name.SetEditable(not name_readonly)
        for control in self._controls_all:
            control.Enable(not is_sqlite)

    def _bind_controls(self) -> None:
        self.model.bind_controls(
            name=self.parent.database_name,
            collation=self.parent.database_collation,
            encryption=self.parent.database_encryption,
            tablespace=self.parent.database_tablespace,
            connection_limit=self.parent.database_connection_limit,
        )

    def _build_controls_all(self) -> list[wx.Window]:
        return [
            self.parent.database_collation,
            self.parent.database_encryption,
            self.parent.database_tablespace,
            self.parent.database_connection_limit,
        ]

    def _build_panel_by_name(self) -> dict[str, wx.Window]:
        return {
            "database_collation_panel": self.parent.database_collation_panel,
            "database_encryption_panel": self.parent.database_encryption_panel,
            "database_tablespace_panel": self.parent.database_tablespace_panel,
            "database_connection_limit_panel": self.parent.database_connection_limit_panel,
            "database_password_panel": self.parent.database_password_panel,
            "database_profile_panel": self.parent.database_profile_panel,
            "database_default_tablespace_panel": self.parent.database_default_tablespace_panel,
            "database_temporary_tablespace_panel": self.parent.database_temporary_tablespace_panel,
            "database_quota_panel": self.parent.database_quota_panel,
            "database_unlimited_quota_panel": self.parent.database_unlimited_quota_panel,
            "database_account_status_panel": self.parent.database_account_status_panel,
            "database_password_expire_panel": self.parent.database_password_expire_panel,
        }

    @staticmethod
    def _get_panel_names_for_engine(engine: Optional[ConnectionEngine]) -> list[str]:
        if engine == ConnectionEngine.MYSQL:
            return [
                "database_collation_panel",
                "database_encryption_panel",
            ]

        if engine == ConnectionEngine.MARIADB:
            return [
                "database_collation_panel",
            ]

        if engine == ConnectionEngine.POSTGRESQL:
            return [
                "database_collation_panel",
                "database_tablespace_panel",
                "database_connection_limit_panel",
            ]

        if engine == ConnectionEngine.ORACLE:
            return [
                "database_password_panel",
                "database_profile_panel",
                "database_default_tablespace_panel",
                "database_temporary_tablespace_panel",
                "database_quota_panel",
                "database_unlimited_quota_panel",
                "database_account_status_panel",
                "database_password_expire_panel",
            ]

        return []

    def _layout_database_options(self) -> None:
        self.parent.m_panel54.Layout()
        if parent := self.parent.m_panel54.GetParent():
            parent.Layout()

    def _populate_choices(self, database, engine: Optional[ConnectionEngine]) -> None:
        if database is None:
            return

        context = database.context if database else None
        collations_source = getattr(context, "COLLATIONS", None) if context else None
        collations = []
        if isinstance(collations_source, dict):
            collations = sorted(str(k) for k in collations_source if k is not None and str(k))

        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB, ConnectionEngine.POSTGRESQL):
            self._apply_choice(
                self.parent.database_collation,
                collations,
                self.model.collation.get_value(),
            )

        if engine == ConnectionEngine.POSTGRESQL:
            tablespace = getattr(database, "tablespace", None)
            self._apply_choice(
                self.parent.database_tablespace,
                [tablespace] if tablespace else [],
                self.model.tablespace.get_value(),
            )
