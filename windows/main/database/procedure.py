from typing import Optional

import wx
import wx.stc

from gettext import gettext as _

from helpers.bindings import AbstractModel, wx_call_after_debounce
from helpers.logger import logger
from helpers.observables import Observable

from structures.connection import ConnectionEngine
from structures.engines.database import SQLProcedure

from windows.main import CURRENT_SESSION, CURRENT_DATABASE, CURRENT_PROCEDURE


class EditViewModel(AbstractModel):
    def __init__(self):
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
        self._build_panel(parent)
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
    # Panel construction
    # ------------------------------------------------------------------

    def _build_panel(self, parent):
        self.panel = wx.Panel(parent.MainFrameNotebook, wx.ID_ANY)
        parent.MainFrameNotebook.AddPage(self.panel, _("Procedure"), False)
        self.page_index = parent.MainFrameNotebook.GetPageCount() - 1

        outer = wx.BoxSizer(wx.VERTICAL)

        # --- Options notebook (mirrors m_notebook7 in views) ---
        self.options_notebook = wx.Notebook(self.panel, wx.ID_ANY)
        self.pnl_options_root = wx.Panel(self.options_notebook, wx.ID_ANY)
        self.options_notebook.AddPage(self.pnl_options_root, _("Options"), False)

        options_vsizer = wx.BoxSizer(wx.VERTICAL)

        # Name row (always visible)
        pnl_name = wx.Panel(self.pnl_options_root, wx.ID_ANY)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_name = wx.StaticText(pnl_name, label=_("Name"))
        lbl_name.SetMinSize(wx.Size(150, -1))
        name_sizer.Add(lbl_name, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.txt_procedure_name = wx.TextCtrl(pnl_name, wx.ID_ANY)
        name_sizer.Add(self.txt_procedure_name, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        pnl_name.SetSizer(name_sizer)
        options_vsizer.Add(pnl_name, 0, wx.EXPAND | wx.ALL, 2)

        # Definer row (MySQL/MariaDB)
        self.pnl_row_definer = wx.Panel(self.pnl_options_root, wx.ID_ANY)
        definer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_def = wx.StaticText(self.pnl_row_definer, label=_("Definer"))
        lbl_def.SetMinSize(wx.Size(150, -1))
        definer_sizer.Add(lbl_def, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.cmb_procedure_definer = wx.ComboBox(self.pnl_row_definer, wx.ID_ANY, style=wx.CB_DROPDOWN)
        definer_sizer.Add(self.cmb_procedure_definer, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        self.pnl_row_definer.SetSizer(definer_sizer)
        options_vsizer.Add(self.pnl_row_definer, 0, wx.EXPAND | wx.ALL, 2)

        # Parameters row (always visible)
        pnl_params = wx.Panel(self.pnl_options_root, wx.ID_ANY)
        params_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_params = wx.StaticText(pnl_params, label=_("Parameters"))
        lbl_params.SetMinSize(wx.Size(150, -1))
        params_sizer.Add(lbl_params, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.txt_procedure_parameters = wx.TextCtrl(pnl_params, wx.ID_ANY)
        params_sizer.Add(self.txt_procedure_parameters, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        pnl_params.SetSizer(params_sizer)
        options_vsizer.Add(pnl_params, 0, wx.EXPAND | wx.ALL, 2)

        # Language row (PostgreSQL)
        self.pnl_row_language = wx.Panel(self.pnl_options_root, wx.ID_ANY)
        lang_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_lang = wx.StaticText(self.pnl_row_language, label=_("Language"))
        lbl_lang.SetMinSize(wx.Size(150, -1))
        lang_sizer.Add(lbl_lang, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.cho_procedure_language = wx.Choice(self.pnl_row_language, wx.ID_ANY, choices=["plpgsql", "sql"])
        self.cho_procedure_language.SetSelection(0)
        lang_sizer.Add(self.cho_procedure_language, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        self.pnl_row_language.SetSizer(lang_sizer)
        options_vsizer.Add(self.pnl_row_language, 0, wx.EXPAND | wx.ALL, 2)

        self.pnl_options_root.SetSizer(options_vsizer)
        self.pnl_options_root.Layout()

        outer.Add(self.options_notebook, 0, wx.ALL | wx.EXPAND, 5)

        # --- Body editor ---
        self.stc_procedure_body = wx.stc.StyledTextCtrl(self.panel, wx.ID_ANY, size=wx.Size(-1, -1))
        self.stc_procedure_body.SetMinSize(wx.Size(-1, 120))
        outer.Add(self.stc_procedure_body, 1, wx.ALL | wx.EXPAND, 5)

        # --- Buttons ---
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_delete_procedure = wx.Button(self.panel, wx.ID_ANY, _("Delete"))
        self.btn_cancel_procedure = wx.Button(self.panel, wx.ID_ANY, _("Cancel"))
        self.btn_save_procedure = wx.Button(self.panel, wx.ID_ANY, _("Save"))
        btn_sizer.Add(self.btn_delete_procedure, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_cancel_procedure, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_save_procedure, 0)
        outer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.panel.SetSizer(outer)

        try:
            from windows.components.stc.styles import apply_stc_theme
            from windows.components.stc.profiles import SQL
            apply_stc_theme(self.stc_procedure_body)
            SQL.apply(self.stc_procedure_body)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Bindings
    # ------------------------------------------------------------------

    def _bind_controls(self):
        self.model.bind_controls(
            name=self.txt_procedure_name,
            parameters=self.txt_procedure_parameters,
            language=self.cho_procedure_language,
            definer=self.cmb_procedure_definer,
            body=self.stc_procedure_body,
        )

    def _bind_buttons(self):
        self.btn_save_procedure.Bind(wx.EVT_BUTTON, self.on_save_procedure)
        self.btn_delete_procedure.Bind(wx.EVT_BUTTON, self.on_delete_procedure)
        self.btn_cancel_procedure.Bind(wx.EVT_BUTTON, self.on_cancel_procedure)

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
            self.btn_save_procedure.Enable(False)
            self.btn_cancel_procedure.Enable(False)
            self.btn_delete_procedure.Enable(False)
        else:
            has_changes = self._has_changes(procedure)
            self.btn_save_procedure.Enable(has_changes)
            self.btn_cancel_procedure.Enable(has_changes)
            self.btn_delete_procedure.Enable(not procedure.is_new)

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
        try:
            logger.debug("ui trace: procedure._populate_definers start engine=%s", engine.name)
            definers = session.context.get_definers()
            self.cmb_procedure_definer.Clear()
            for definer in definers:
                self.cmb_procedure_definer.Append(definer)
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

        self.pnl_options_root.GetSizer().Layout()
        self.options_notebook.SetMinSize(wx.Size(-1, -1))
        self.options_notebook.Fit()
        self.panel.Layout()

    def _apply_mysql_visibility(self):
        self._batch_show_hide(
            show=[self.pnl_row_definer],
            hide=[self.pnl_row_language],
        )

    def _apply_postgresql_visibility(self):
        self._batch_show_hide(
            show=[self.pnl_row_language],
            hide=[self.pnl_row_definer],
        )

    def _apply_default_visibility(self):
        self._batch_show_hide(
            show=[],
            hide=[self.pnl_row_definer, self.pnl_row_language],
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
