from typing import Optional

import wx

from gettext import gettext as _

from helpers.bindings import AbstractModel, wx_call_after_debounce
from helpers.logger import logger
from helpers.observables import Observable

from structures.connection import ConnectionEngine
from structures.engines.database import SQLProcedure

from windows.main import CURRENT_SESSION, CURRENT_DATABASE, CURRENT_PROCEDURE


class EditViewModel(AbstractModel):
    def __init__(self):
        super().__init__()

        self.name = Observable()
        self.parameters = Observable()
        self.language = Observable()
        self.definer = Observable()
        self.body = Observable()

        wx_call_after_debounce(
            self.name, self.parameters, self.language, self.definer, self.body,
            callback=self.update_procedure
        )

        CURRENT_PROCEDURE.subscribe(self._load_procedure)

    def _load_procedure(self, procedure: Optional[SQLProcedure]):
        if procedure is None:
            return

        self.name.set_initial(procedure.name)
        self.parameters.set_initial(getattr(procedure, "parameters", ""))
        self.body.set_initial(getattr(procedure, "statement", ""))

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        engine = session.engine
        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._load_mysql_fields(procedure)
        elif engine == ConnectionEngine.POSTGRESQL:
            self._load_postgresql_fields(procedure)

    def update_procedure(self, *args):
        if not any(args):
            return

        procedure = CURRENT_PROCEDURE.get_value()
        if not procedure:
            return

        procedure.name = self.name.get_value() or procedure.name
        if hasattr(procedure, "parameters"):
            procedure.parameters = self.parameters.get_value() or ""
        if hasattr(procedure, "statement"):
            procedure.statement = self.body.get_value() or ""

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        engine = session.engine
        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._update_mysql_fields(procedure)
        elif engine == ConnectionEngine.POSTGRESQL:
            self._update_postgresql_fields(procedure)

    def _load_mysql_fields(self, procedure: SQLProcedure):
        if hasattr(procedure, "definer"):
            self.definer.set_initial(procedure.definer)

    def _load_postgresql_fields(self, procedure: SQLProcedure):
        if hasattr(procedure, "language"):
            self.language.set_initial(procedure.language)

    def _update_mysql_fields(self, procedure: SQLProcedure):
        if hasattr(procedure, "definer"):
            procedure.definer = self.definer.get_value() or ""

    def _update_postgresql_fields(self, procedure: SQLProcedure):
        if hasattr(procedure, "language"):
            procedure.language = self.language.get_value() or "plpgsql"


class ProcedureEditorController:
    def __init__(self, parent):
        self.parent = parent

        try:
            from windows.components.stc.styles import apply_stc_theme
            from windows.components.stc.profiles import SQL
            apply_stc_theme(self.parent.stc_procedure)
            SQL.apply(self.parent.stc_procedure)
        except Exception:
            pass

        self.model = EditViewModel()
        self._bind_controls()
        self._bind_buttons()

        wx_call_after_debounce(
            self.model.name, self.model.parameters,
            self.model.language, self.model.definer, self.model.body,
            callback=self.update_button_states
        )

        CURRENT_PROCEDURE.subscribe(self.on_current_procedure_changed)

    # ------------------------------------------------------------------
    # Bindings
    # ------------------------------------------------------------------

    def _bind_controls(self):
        self.model.bind_controls(
            name=self.parent.txt_name_procedure,
            body=self.parent.stc_procedure,
        )

    def _bind_buttons(self):
        self.parent.btn_save_procedure.Bind(wx.EVT_BUTTON, self.on_save_procedure)
        self.parent.btn_delete_procedure.Bind(wx.EVT_BUTTON, self.on_delete_procedure)
        self.parent.btn_cancel_procedure.Bind(wx.EVT_BUTTON, self.on_cancel_procedure)

    # ------------------------------------------------------------------
    # Button state
    # ------------------------------------------------------------------

    def _get_original_procedure(self, procedure: SQLProcedure) -> Optional[SQLProcedure]:
        if procedure.is_new:
            return None
        database = CURRENT_DATABASE.get_value()
        if not database:
            return None
        return next((p for p in database.procedures if p.id == procedure.id), None)

    def _has_changes(self, procedure: SQLProcedure) -> bool:
        if procedure.is_new:
            return True
        original = self._get_original_procedure(procedure)
        if original is None:
            return True
        self.model.update_procedure(procedure)
        return procedure != original

    def update_button_states(self, *args, **kwargs):
        procedure = CURRENT_PROCEDURE.get_value()
        logger.debug(
            "ui trace: procedure.update_button_states procedure=%s is_new=%s",
            getattr(procedure, "name", None) if procedure is not None else None,
            getattr(procedure, "is_new", None) if procedure is not None else None,
        )
        if procedure is None:
            self.parent.btn_save_procedure.Enable(False)
            self.parent.btn_cancel_procedure.Enable(False)
            self.parent.btn_delete_procedure.Enable(False)
        else:
            has_changes = self._has_changes(procedure)
            self.parent.btn_save_procedure.Enable(has_changes)
            self.parent.btn_cancel_procedure.Enable(has_changes)
            self.parent.btn_delete_procedure.Enable(not procedure.is_new)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def on_save_procedure(self, event):
        self.do_save_procedure()

    def on_delete_procedure(self, event):
        self.do_delete_procedure()

    def on_cancel_procedure(self, event):
        self.do_cancel_procedure()

    def do_save_procedure(self):
        procedure = CURRENT_PROCEDURE.get_value()
        if not procedure:
            return
        session = CURRENT_SESSION.get_value()
        if not session:
            return

        is_new = procedure.is_new
        try:
            procedure.save()
            message = _("Procedure created successfully") if is_new else _("Procedure updated successfully")
            wx.MessageBox(message, _("Success"), wx.OK | wx.ICON_INFORMATION)
            self.parent.controller_tree_connections.refresh_current_database()
            if is_new:
                database = CURRENT_DATABASE.get_value()
                saved = next((p for p in database.procedures if p.name == procedure.name), None)
                if saved:
                    CURRENT_PROCEDURE.set_value(None)
                    CURRENT_PROCEDURE.set_value(saved)
                    return
            self.update_button_states()
        except Exception as e:
            wx.MessageBox(_("Error saving procedure: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)

    def do_delete_procedure(self):
        procedure = CURRENT_PROCEDURE.get_value()
        if not procedure:
            return
        session = CURRENT_SESSION.get_value()
        if not session:
            return

        result = wx.MessageBox(
            _("Are you sure you want to delete procedure '{}'?").format(procedure.name),
            _("Confirm Delete"),
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if result != wx.YES:
            return

        try:
            procedure.drop()
            wx.MessageBox(_("Procedure deleted successfully"), _("Success"), wx.OK | wx.ICON_INFORMATION)
            CURRENT_PROCEDURE.set_value(None)
            database = CURRENT_DATABASE.get_value()
            database.procedures.refresh()
            self.parent.controller_tree_connections.refresh_current_database()
        except Exception as e:
            wx.MessageBox(_("Error deleting procedure: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)

    def do_cancel_procedure(self):
        procedure = CURRENT_PROCEDURE.get_value()
        if not procedure:
            return
        CURRENT_PROCEDURE.set_value(None)
        CURRENT_PROCEDURE.set_value(procedure)
        self.update_button_states()

    # ------------------------------------------------------------------
    # Current procedure changed
    # ------------------------------------------------------------------

    def on_current_procedure_changed(self, procedure: Optional[SQLProcedure]):
        logger.debug(
            "ui trace: procedure.on_current_procedure_changed procedure=%s is_new=%s",
            getattr(procedure, "name", None) if procedure is not None else None,
            getattr(procedure, "is_new", None) if procedure is not None else None,
        )
        self.update_button_states()

        if procedure is None:
            return

        session = CURRENT_SESSION.get_value()
        if session:
            engine = session.engine
            self.apply_engine_visibility(engine)
            self._populate_definers(engine, session)

    def _populate_definers(self, engine: ConnectionEngine, session):
        if engine not in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            return
        cmb = getattr(self.parent, 'cmb_procedure_definer', None)
        if cmb is None:
            return
        try:
            logger.debug("ui trace: procedure._populate_definers start engine=%s", engine.name)
            definers = session.context.get_definers()
            cmb.Clear()
            for definer in definers:
                cmb.Append(definer)
            logger.debug("ui trace: procedure._populate_definers done count=%s", len(definers))
        except Exception:
            pass

    def apply_engine_visibility(self, engine: ConnectionEngine):
        logger.debug("ui trace: procedure.apply_engine_visibility engine=%s", engine.name)
        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._apply_mysql_visibility()
        elif engine == ConnectionEngine.POSTGRESQL:
            self._apply_postgresql_visibility()
        else:
            self._apply_default_visibility()

        self.parent.m_panel73.GetSizer().Layout()
        self.parent.panel_procedures.Layout()

    def _apply_mysql_visibility(self):
        definer = getattr(self.parent, 'pnl_procedure_row_definer', None)
        language = getattr(self.parent, 'pnl_procedure_row_language', None)
        self._batch_show_hide(
            show=[w for w in [definer] if w],
            hide=[w for w in [language] if w],
        )

    def _apply_postgresql_visibility(self):
        definer = getattr(self.parent, 'pnl_procedure_row_definer', None)
        language = getattr(self.parent, 'pnl_procedure_row_language', None)
        self._batch_show_hide(
            show=[w for w in [language] if w],
            hide=[w for w in [definer] if w],
        )

    def _apply_default_visibility(self):
        definer = getattr(self.parent, 'pnl_procedure_row_definer', None)
        language = getattr(self.parent, 'pnl_procedure_row_language', None)
        self._batch_show_hide(
            show=[],
            hide=[w for w in [definer, language] if w],
        )

    def _batch_show_hide(self, show: list[wx.Window], hide: list[wx.Window]):
        for widget in show:
            widget.Show(True)
            sizer = widget.GetContainingSizer()
            if sizer:
                sizer.Show(widget, True)
        for widget in hide:
            widget.Show(False)
            sizer = widget.GetContainingSizer()
            if sizer:
                sizer.Show(widget, False)
