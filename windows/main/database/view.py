from typing import Optional

import wx
import wx.stc

from gettext import gettext as _

from helpers.sql import format_sql
from helpers.bindings import AbstractModel, wx_call_after_debounce
from helpers.observables import Observable

from structures.connection import ConnectionEngine
from structures.engines.database import SQLView

from windows.main import CURRENT_SESSION, CURRENT_DATABASE, CURRENT_VIEW


class EditViewModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.schema = Observable()
        self.definer = Observable()
        self.sql_security = Observable()
        self.algorithm = Observable()
        self.constraint = Observable()
        self.security_barrier = Observable()
        self.force = Observable()
        self.select_statement = Observable()

        wx_call_after_debounce(
            self.name, self.schema, self.definer, self.sql_security,
            self.algorithm, self.constraint, self.security_barrier,
            self.force, self.select_statement,
            callback=self.update_view
        )

        CURRENT_VIEW.subscribe(self._load_view)

    def _load_view(self, view: Optional[SQLView]):
        if view is None:
            return

        self.name.set_initial(view.name)
        
        if session := CURRENT_SESSION.get_value() :
            dialect = session.engine.value.dialect
            formatted_sql = format_sql(view.statement, dialect)
            self.select_statement.set_initial(formatted_sql)
        else:
            self.select_statement.set_initial(view.statement)

        if not session:
            return

        engine = session.engine

        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._load_mysql_fields(view)
        elif engine == ConnectionEngine.POSTGRESQL:
            self._load_postgresql_fields(view)
        elif engine == ConnectionEngine.ORACLE:
            self._load_oracle_fields(view)

    def update_view(self, *args):
        if not any(args):
            return

        view = CURRENT_VIEW.get_value()
        if not view:
            return

        view.name = self.name.get_value()
        view.statement = self.select_statement.get_value()

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        engine = session.engine

        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._update_mysql_fields(view)
        elif engine == ConnectionEngine.POSTGRESQL:
            self._update_postgresql_fields(view)
        elif engine == ConnectionEngine.ORACLE:
            self._update_oracle_fields(view)

    def _load_mysql_fields(self, view: SQLView):
        if hasattr(view, "definer"):
            self.definer.set_initial(view.definer)
        if hasattr(view, "sql_security"):
            self.sql_security.set_initial(view.sql_security)
        if hasattr(view, "algorithm"):
            self.algorithm.set_initial(view.algorithm)
        if hasattr(view, "constraint"):
            self.constraint.set_initial(view.constraint)

    def _load_postgresql_fields(self, view: SQLView):
        if hasattr(view, "schema"):
            self.schema.set_initial(view.schema)
        if hasattr(view, "constraint"):
            self.constraint.set_initial(view.constraint)
        if hasattr(view, "security_barrier"):
            self.security_barrier.set_initial(view.security_barrier)

    def _load_oracle_fields(self, view: SQLView):
        if hasattr(view, "schema"):
            self.schema.set_initial(view.schema)
        if hasattr(view, "constraint"):
            self.constraint.set_initial(view.constraint)
        if hasattr(view, "force"):
            self.force.set_initial(view.force)

    def _update_mysql_fields(self, view: SQLView):
        if hasattr(view, "definer"):
            view.definer = self.definer.get_value()
        if hasattr(view, "sql_security"):
            view.sql_security = self.sql_security.get_value()
        if hasattr(view, "algorithm"):
            view.algorithm = self.algorithm.get_value()
        if hasattr(view, "constraint"):
            view.constraint = self.constraint.get_value()

    def _update_postgresql_fields(self, view: SQLView):
        if hasattr(view, "schema"):
            view.schema = self.schema.get_value()
        if hasattr(view, "constraint"):
            view.constraint = self.constraint.get_value()
        if hasattr(view, "security_barrier"):
            view.security_barrier = self.security_barrier.get_value()

    def _update_oracle_fields(self, view: SQLView):
        if hasattr(view, "schema"):
            view.schema = self.schema.get_value()
        if hasattr(view, "constraint"):
            view.constraint = self.constraint.get_value()
        if hasattr(view, "force"):
            view.force = self.force.get_value()


class ViewEditorController:
    def __init__(self, parent):
        self.parent = parent
        self.model = EditViewModel()
        
        self._bind_controls()
        self._bind_buttons()
        
        wx_call_after_debounce(
            self.model.name,
            self.model.schema,
            self.model.definer,
            self.model.sql_security,
            self.model.algorithm,
            self.model.constraint,
            self.model.security_barrier,
            self.model.force,
            self.model.select_statement,
            callback=self.update_button_states
        )

        CURRENT_VIEW.subscribe(self.on_current_view_changed)


    def _bind_controls(self):
        algorithm_radios = [
            self.parent.rad_view_algorithm_undefined,
            self.parent.rad_view_algorithm_merge,
            self.parent.rad_view_algorithm_temptable,
        ]
        
        constraint_radios = [
            self.parent.rad_view_constraint_none,
            self.parent.rad_view_constraint_local,
            self.parent.rad_view_constraint_cascaded,
            self.parent.rad_view_constraint_check_only,
            self.parent.rad_view_constraint_read_only,
        ]
        
        self.model.bind_controls(
            name=self.parent.txt_view_name,
            schema=self.parent.cho_view_schema,
            definer=self.parent.cmb_view_definer,
            sql_security=self.parent.cho_view_sql_security,
            algorithm=algorithm_radios,
            constraint=constraint_radios,
            security_barrier=self.parent.chk_view_security_barrier,
            force=self.parent.chk_view_force,
            select_statement=self.parent.stc_view_select,
        )

    def _bind_buttons(self):
        self.parent.btn_save_view.Bind(wx.EVT_BUTTON, self.on_save_view)
        self.parent.btn_delete_view.Bind(wx.EVT_BUTTON, self.on_delete_view)
        self.parent.btn_cancel_view.Bind(wx.EVT_BUTTON, self.on_cancel_view)

    def _get_original_view(self, view: SQLView) -> Optional[SQLView]:
        if view.is_new:
            return None
        
        session = CURRENT_SESSION.get_value()
        database = CURRENT_DATABASE.get_value()
        if not session or not database:
            return None
        
        return next((v for v in database.views if v.id == view.id), None)

    def _has_changes(self, view: SQLView) -> bool:
        if view.is_new:
            return True
        
        original = self._get_original_view(view)
        if original is None:
            return True
        
        self.model.update_view(view)
        return view != original

    def update_button_states(self):
        view = CURRENT_VIEW.get_value()
        
        if view is None:
            self.parent.btn_save_view.Enable(False)
            self.parent.btn_cancel_view.Enable(False)
            self.parent.btn_delete_view.Enable(False)
        else:
            has_changes = self._has_changes(view)
            self.parent.btn_save_view.Enable(has_changes)
            self.parent.btn_cancel_view.Enable(has_changes)
            self.parent.btn_delete_view.Enable(not view.is_new)

    def on_save_view(self, event):
        self.do_save_view()

    def on_delete_view(self, event):
        self.do_delete_view()

    def on_cancel_view(self, event):
        self.do_cancel_view()

    def do_save_view(self):
        view = CURRENT_VIEW.get_value()
        if not view:
            return

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        try:
            view.save()
            message = _("View created successfully") if view.is_new else _("View updated successfully")
            wx.MessageBox(message, _("Success"), wx.OK | wx.ICON_INFORMATION)
            self.update_button_states()
        except Exception as e:
            wx.MessageBox(_("Error saving view: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)


    def do_delete_view(self):
        view = CURRENT_VIEW.get_value()
        if not view:
            return

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        result = wx.MessageBox(
            _("Are you sure you want to delete view '{}'?").format(view.name),
            _("Confirm Delete"),
            wx.YES_NO | wx.ICON_QUESTION
        )

        if result != wx.YES:
            return

        try:
            view.drop()
            wx.MessageBox(_("View deleted successfully"), _("Success"), wx.OK | wx.ICON_INFORMATION)
            CURRENT_VIEW.set_value(None)
        except Exception as e:
            wx.MessageBox(_("Error deleting view: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)

    def do_cancel_view(self):
        view = CURRENT_VIEW.get_value()
        if not view:
            return

        CURRENT_VIEW.set_value(None)
        CURRENT_VIEW.set_value(view)
        self.update_button_states()

    def on_current_view_changed(self, view: Optional[SQLView]):
        self.update_button_states()
        
        if view is None:
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
            definers = session.context.get_definers()
            self.parent.cmb_view_definer.Clear()
            for definer in definers:
                self.parent.cmb_view_definer.Append(definer)
        except Exception:
            pass

    def apply_engine_visibility(self, engine: ConnectionEngine):
        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._apply_mysql_visibility()
        elif engine == ConnectionEngine.POSTGRESQL:
            self._apply_postgresql_visibility()
        elif engine == ConnectionEngine.ORACLE:
            self._apply_oracle_visibility()
        elif engine == ConnectionEngine.SQLITE:
            self._apply_sqlite_visibility()
        
        self.parent.pnl_view_editor_root.GetSizer().Layout()
        self.parent.m_notebook7.SetMinSize(wx.Size(-1, -1))
        self.parent.m_notebook7.Fit()
        self.parent.panel_views.Layout()

    def _apply_mysql_visibility(self):
        panels_to_show = [
            self.parent.pnl_row_definer,
            self.parent.pnl_row_sql_security,
            self.parent.pnl_row_algorithm,
            self.parent.pnl_row_constraint,
        ]
        panels_to_hide = [
            self.parent.pnl_row_schema,
            self.parent.pnl_row_security_barrier,
            self.parent.pnl_row_force,
        ]
        self._batch_show_hide(panels_to_show, panels_to_hide)
        
        self.parent.rad_view_constraint_none.Show(True)
        self.parent.rad_view_constraint_local.Show(True)
        self.parent.rad_view_constraint_cascaded.Show(True)
        self.parent.rad_view_constraint_check_only.Show(False)
        self.parent.rad_view_constraint_read_only.Show(False)
        
        self._normalize_radio_selection_algorithm()
        self._normalize_radio_selection_constraint()

    def _apply_postgresql_visibility(self):
        panels_to_show = [
            self.parent.pnl_row_schema,
            self.parent.pnl_row_constraint,
            self.parent.pnl_row_force,
        ]
        panels_to_hide = [
            self.parent.pnl_row_definer,
            self.parent.pnl_row_sql_security,
            self.parent.pnl_row_algorithm,
            self.parent.pnl_row_security_barrier,
        ]
        self._batch_show_hide(panels_to_show, panels_to_hide)
        
        self.parent.rad_view_constraint_none.Show(True)
        self.parent.rad_view_constraint_local.Show(True)
        self.parent.rad_view_constraint_cascaded.Show(True)
        self.parent.rad_view_constraint_check_only.Show(False)
        self.parent.rad_view_constraint_read_only.Show(False)
        
        self._normalize_radio_selection_constraint()

    def _apply_oracle_visibility(self):
        panels_to_show = [
            self.parent.pnl_row_schema,
            self.parent.pnl_row_constraint,
            self.parent.pnl_row_security_barrier,
        ]
        panels_to_hide = [
            self.parent.pnl_row_definer,
            self.parent.pnl_row_sql_security,
            self.parent.pnl_row_algorithm,
            self.parent.pnl_row_force,
        ]
        self._batch_show_hide(panels_to_show, panels_to_hide)
        
        self.parent.rad_view_constraint_none.Show(True)
        self.parent.rad_view_constraint_local.Show(False)
        self.parent.rad_view_constraint_cascaded.Show(False)
        self.parent.rad_view_constraint_check_only.Show(True)
        self.parent.rad_view_constraint_read_only.Show(True)
        
        self._normalize_radio_selection_constraint()

    def _apply_sqlite_visibility(self):
        panels_to_hide = [
            self.parent.pnl_row_schema,
            self.parent.pnl_row_definer,
            self.parent.pnl_row_sql_security,
            self.parent.pnl_row_algorithm,
            self.parent.pnl_row_constraint,
            self.parent.pnl_row_security_barrier,
            self.parent.pnl_row_force,
        ]
        self._batch_show_hide([], panels_to_hide)

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

    def _normalize_radio_selection_algorithm(self):
        radios = [
            self.parent.rad_view_algorithm_undefined,
            self.parent.rad_view_algorithm_merge,
            self.parent.rad_view_algorithm_temptable,
        ]
        self._normalize_radio_group(radios)

    def _normalize_radio_selection_constraint(self):
        radios = [
            self.parent.rad_view_constraint_none,
            self.parent.rad_view_constraint_local,
            self.parent.rad_view_constraint_cascaded,
            self.parent.rad_view_constraint_check_only,
            self.parent.rad_view_constraint_read_only,
        ]
        self._normalize_radio_group(radios)

    def _normalize_radio_group(self, radios: list[wx.RadioButton]):
        visible = [r for r in radios if r.IsShown()]
        
        if not visible:
            return
        
        selected = next((r for r in visible if r.GetValue()), None)
        
        if selected is None:
            visible[0].SetValue(True)

