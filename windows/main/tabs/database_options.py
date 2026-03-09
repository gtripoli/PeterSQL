from typing import Optional

import wx

from helpers.bindings import AbstractModel
from helpers.observables import Observable, debounce

from structures.connection import ConnectionEngine

from windows.main import CURRENT_DATABASE, CURRENT_SESSION


class EditDatabaseOptionsModel(AbstractModel):
    def __init__(self):
        self.database_name = Observable()
        self.database_character_set = Observable()
        self.database_collation = Observable()
        self.database_encryption = Observable(False)
        self.database_read_only = Observable(False)
        self.database_tablespace = Observable()
        self.database_connection_limit = Observable(0)
        self.database_password = Observable()
        self.database_profile = Observable()
        self.database_default_tablespace = Observable()
        self.database_temporary_tablespace = Observable()
        self.database_quota = Observable()
        self.database_unlimited_quota = Observable(False)
        self.database_account_status = Observable()
        self.database_password_expire = Observable(False)

        debounce(
            self.database_name,
            self.database_character_set,
            self.database_collation,
            self.database_encryption,
            self.database_read_only,
            self.database_tablespace,
            self.database_connection_limit,
            self.database_password,
            self.database_profile,
            self.database_default_tablespace,
            self.database_temporary_tablespace,
            self.database_quota,
            self.database_unlimited_quota,
            self.database_account_status,
            self.database_password_expire,
            callback=self._update_database,
        )

        CURRENT_DATABASE.subscribe(self._load_database)

    @staticmethod
    def _first_attr(source, names: list[str], default=None):
        if source is None:
            return default

        for name in names:
            if hasattr(source, name):
                value = getattr(source, name)
                if value is not None:
                    return value

        return default

    @staticmethod
    def _encryption_to_bool(value) -> bool:
        if isinstance(value, bool):
            return value

        if value is None:
            return False

        return str(value).strip().upper() in ["Y", "YES", "TRUE", "1", "ON"]

    def _load_database(self, database) -> None:
        self.database_name.set_initial(self._first_attr(database, ["name"], ""))
        self.database_collation.set_initial(
            self._first_attr(database, ["default_collation", "collation", "collation_name"], "")
        )

        context = database.context if database else None
        charset = None
        if context and self.database_collation.get_value() and getattr(context, "COLLATIONS", None):
            charset = context.COLLATIONS.get(self.database_collation.get_value())

        self.database_character_set.set_initial(
            charset or self._first_attr(database, ["character_set", "charset"], "")
        )

        self.database_encryption.set_initial(
            self._encryption_to_bool(self._first_attr(database, ["encryption"], None))
        )
        self.database_read_only.set_initial(bool(self._first_attr(database, ["read_only", "is_read_only"], False)))
        self.database_tablespace.set_initial(self._first_attr(database, ["tablespace", "default_tablespace"], ""))
        self.database_connection_limit.set_initial(int(self._first_attr(database, ["connection_limit"], 0) or 0))
        self.database_password.set_initial(self._first_attr(database, ["password"], ""))
        self.database_profile.set_initial(self._first_attr(database, ["profile"], ""))
        self.database_default_tablespace.set_initial(self._first_attr(database, ["default_tablespace"], ""))
        self.database_temporary_tablespace.set_initial(self._first_attr(database, ["temporary_tablespace"], ""))
        self.database_quota.set_initial(self._first_attr(database, ["quota"], ""))
        self.database_unlimited_quota.set_initial(bool(self._first_attr(database, ["unlimited_quota"], False)))
        self.database_account_status.set_initial(self._first_attr(database, ["account_status"], ""))
        self.database_password_expire.set_initial(bool(self._first_attr(database, ["password_expire"], False)))

    def _update_database(self, *args) -> None:
        if not any(arg is not None for arg in args):
            return

        database = CURRENT_DATABASE.get_value()
        if database is None:
            return

        session = CURRENT_SESSION.get_value()
        engine = session.engine if session else None

        encryption_value = self.database_encryption.get_value()
        if engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB]:
            encryption_value = "Y" if bool(encryption_value) else "N"

        if hasattr(database, "name"):
            database.name = self.database_name.get_value()

        mapping = {
            "character_set": self.database_character_set.get_value(),
            "charset": self.database_character_set.get_value(),
            "default_collation": self.database_collation.get_value(),
            "collation": self.database_collation.get_value(),
            "collation_name": self.database_collation.get_value(),
            "encryption": encryption_value,
            "read_only": self.database_read_only.get_value(),
            "is_read_only": self.database_read_only.get_value(),
            "tablespace": self.database_tablespace.get_value(),
            "default_tablespace": self.database_default_tablespace.get_value(),
            "temporary_tablespace": self.database_temporary_tablespace.get_value(),
            "connection_limit": self.database_connection_limit.get_value(),
            "password": self.database_password.get_value(),
            "profile": self.database_profile.get_value(),
            "quota": self.database_quota.get_value(),
            "unlimited_quota": self.database_unlimited_quota.get_value(),
            "account_status": self.database_account_status.get_value(),
            "password_expire": self.database_password_expire.get_value(),
        }

        for attr, value in mapping.items():
            if hasattr(database, attr):
                setattr(database, attr, value)


class DatabaseOptionsController:
    def __init__(self, parent):
        self.parent = parent
        self.model = EditDatabaseOptionsModel()
        self._panel_by_name = self._build_panel_by_name()
        self._panels_all = list(self._panel_by_name.values())
        self._controls_all = self._build_controls_all()

        self._bind_controls()

        CURRENT_SESSION.subscribe(self._on_current_session)
        CURRENT_DATABASE.subscribe(self._on_current_database)

        self.apply_for_current_state()

    @staticmethod
    def _first_attr(source, names: list[str], default=None):
        if source is None:
            return default

        for name in names:
            if hasattr(source, name):
                value = getattr(source, name)
                if value is not None:
                    return value

        return default

    def _apply_choice(self, choice: wx.Choice, items: list[str], selected: Optional[str]) -> None:
        normalized = [str(item) for item in items if item is not None and str(item)]

        if selected is not None and str(selected) and str(selected) not in normalized:
            normalized.append(str(selected))

        choice.SetItems(normalized)

        if not normalized:
            return

        if selected and choice.SetStringSelection(str(selected)):
            return

        choice.SetSelection(0)

    def _apply_engine(self, engine: Optional[ConnectionEngine]) -> None:
        panel_names = self._get_panel_names_for_engine(engine)
        visible_panels = [self._panel_by_name[name] for name in panel_names]

        self._batch_show_hide(show=visible_panels, hide=self._panels_all)
        self._apply_readonly_rules(engine)
        self._layout_database_options()

    def _apply_readonly_rules(self, engine: Optional[ConnectionEngine]) -> None:
        is_sqlite = engine == ConnectionEngine.SQLITE

        self.parent.database_name.Enable(True)
        self.parent.database_name.SetEditable(not is_sqlite)
        self._set_controls_enabled(enabled=not is_sqlite)

    def _batch_show_hide(self, show: list[wx.Window], hide: list[wx.Window]) -> None:
        show_set = set(show)
        for panel in hide:
            panel.Show(panel in show_set)

    def _bind_controls(self) -> None:
        self.model.bind_controls(
            database_name=self.parent.database_name,
            database_character_set=self.parent.database_character_set,
            database_collation=self.parent.database_collation,
            database_encryption=self.parent.database_encryption,
            database_read_only=self.parent.database_read_only,
            database_tablespace=self.parent.database_tablespace,
            database_connection_limit=self.parent.database_connection_limit,
            database_password=self.parent.m_textCtrl36,
            database_profile=self.parent.database_profile,
            database_default_tablespace=self.parent.database_default_tablespace,
            database_temporary_tablespace=self.parent.database_temporary_tablespace,
            database_quota=self.parent.database_quota,
            database_unlimited_quota=self.parent.database_unlimited_quota,
            database_account_status=self.parent.database_account_status,
            database_password_expire=self.parent.database_password_expire,
        )

    def _build_controls_all(self) -> list[wx.Window]:
        return [
            self.parent.database_character_set,
            self.parent.database_collation,
            self.parent.database_encryption,
            self.parent.database_read_only,
            self.parent.database_tablespace,
            self.parent.database_connection_limit,
            self.parent.m_textCtrl36,
            self.parent.database_profile,
            self.parent.database_default_tablespace,
            self.parent.database_temporary_tablespace,
            self.parent.database_quota,
            self.parent.database_unlimited_quota,
            self.parent.database_account_status,
            self.parent.database_password_expire,
        ]

    def _build_panel_by_name(self) -> dict[str, wx.Window]:
        return {
            "database_character_set_panel": self.parent.database_character_set_panel,
            "database_collation_panel": self.parent.database_collation_panel,
            "database_encryption_panel": self.parent.database_encryption_panel,
            "database_read_only_panel": self.parent.database_read_only_panel,
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

    def _get_panel_names_for_engine(self, engine: Optional[ConnectionEngine]) -> list[str]:
        if engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB]:
            return [
                "database_character_set_panel",
                "database_collation_panel",
                "database_encryption_panel",
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

    def _on_current_database(self, database) -> None:
        self.apply_for_current_state()

    def _on_current_session(self, session) -> None:
        self.apply_for_current_state()

    def _populate_choices(self, database) -> None:
        context = database.context if database else None

        collations = []
        if context and getattr(context, "COLLATIONS", None):
            collations = sorted(context.COLLATIONS.keys())

        charsets = []
        if context and getattr(context, "COLLATIONS", None):
            charsets = sorted(set(context.COLLATIONS.values()))

        self._apply_choice(
            self.parent.database_character_set,
            charsets,
            self.model.database_character_set.get_value(),
        )
        self._apply_choice(
            self.parent.database_collation,
            collations,
            self.model.database_collation.get_value(),
        )

        self._apply_choice(
            self.parent.database_tablespace,
            [self._first_attr(database, ["tablespace", "default_tablespace"])],
            self.model.database_tablespace.get_value(),
        )
        self._apply_choice(
            self.parent.database_profile,
            [self._first_attr(database, ["profile"])],
            self.model.database_profile.get_value(),
        )
        self._apply_choice(
            self.parent.database_default_tablespace,
            [self._first_attr(database, ["default_tablespace"])],
            self.model.database_default_tablespace.get_value(),
        )
        self._apply_choice(
            self.parent.database_temporary_tablespace,
            [self._first_attr(database, ["temporary_tablespace"])],
            self.model.database_temporary_tablespace.get_value(),
        )
        self._apply_choice(
            self.parent.database_account_status,
            [self._first_attr(database, ["account_status"])],
            self.model.database_account_status.get_value(),
        )

    def _set_controls_enabled(self, enabled: bool) -> None:
        for control in self._controls_all:
            control.Enable(enabled)

    def apply_for_current_state(self) -> None:
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        engine = session.engine if session else None

        self._populate_choices(database)
        self._apply_engine(engine)
