from typing import Optional

import wx
import wx.stc

from helpers.bindings import AbstractModel
from helpers.observables import Observable, debounce

from structures.engines.database import SQLView

from windows.main import CURRENT_SESSION, CURRENT_VIEW


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

        debounce(
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
        self.select_statement.set_initial(view.sql)

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        engine = session.engine.value.name.lower()

        if engine in ["mysql", "mariadb"]:
            self._load_mysql_fields(view)
        elif engine == "postgresql":
            self._load_postgresql_fields(view)
        elif engine == "oracle":
            self._load_oracle_fields(view)

    def update_view(self, *args):
        if not any(args):
            return

        view = CURRENT_VIEW.get_value()
        if not view:
            return

        view.name = self.name.get_value()
        view.sql = self.select_statement.get_value()

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        engine = session.engine.value.name.lower()

        if engine in ["mysql", "mariadb"]:
            self._update_mysql_fields(view)
        elif engine == "postgresql":
            self._update_postgresql_fields(view)
        elif engine == "oracle":
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

    def on_current_view_changed(self, view: Optional[SQLView]):
        if view is None:
            return
        
        session = CURRENT_SESSION.get_value()
        if session:
            engine = session.engine.value.name.lower()
            self.apply_engine_visibility(engine)

    def apply_engine_visibility(self, engine: str):
        if engine in ["mysql", "mariadb"]:
            self._apply_mysql_visibility()
        elif engine == "postgresql":
            self._apply_postgresql_visibility()
        elif engine == "oracle":
            self._apply_oracle_visibility()
        elif engine == "sqlite":
            self._apply_sqlite_visibility()
        
        self.parent.pnl_view_editor_root.Layout()

    def _apply_mysql_visibility(self):
        widgets_to_show = [
            self.parent.cmb_view_definer,
            self.parent.lbl_view_definer,
            self.parent.cho_view_sql_security,
            self.parent.lbl_view_sql_security,
            self.parent.rad_view_algorithm_undefined,
            self.parent.rad_view_algorithm_merge,
            self.parent.rad_view_algorithm_temptable,
            self.parent.rad_view_constraint_none,
            self.parent.rad_view_constraint_local,
            self.parent.rad_view_constraint_cascaded,
        ]
        widgets_to_hide = [
            self.parent.cho_view_schema,
            self.parent.lbl_view_schema,
            self.parent.rad_view_constraint_check_only,
            self.parent.rad_view_constraint_read_only,
            self.parent.chk_view_security_barrier,
            self.parent.chk_view_force,
        ]
        self._batch_show_hide(widgets_to_show, widgets_to_hide)
        self._normalize_radio_selection_algorithm()
        self._normalize_radio_selection_constraint()

    def _apply_postgresql_visibility(self):
        widgets_to_show = [
            self.parent.cho_view_schema,
            self.parent.lbl_view_schema,
            self.parent.rad_view_constraint_none,
            self.parent.rad_view_constraint_local,
            self.parent.rad_view_constraint_cascaded,
            self.parent.chk_view_security_barrier,
        ]
        widgets_to_hide = [
            self.parent.cmb_view_definer,
            self.parent.lbl_view_definer,
            self.parent.cho_view_sql_security,
            self.parent.lbl_view_sql_security,
            self.parent.rad_view_algorithm_undefined,
            self.parent.rad_view_algorithm_merge,
            self.parent.rad_view_algorithm_temptable,
            self.parent.rad_view_constraint_check_only,
            self.parent.rad_view_constraint_read_only,
            self.parent.chk_view_force,
        ]
        self._batch_show_hide(widgets_to_show, widgets_to_hide)
        self._normalize_radio_selection_constraint()

    def _apply_oracle_visibility(self):
        widgets_to_show = [
            self.parent.cho_view_schema,
            self.parent.lbl_view_schema,
            self.parent.rad_view_constraint_none,
            self.parent.rad_view_constraint_check_only,
            self.parent.rad_view_constraint_read_only,
            self.parent.chk_view_force,
        ]
        widgets_to_hide = [
            self.parent.cmb_view_definer,
            self.parent.lbl_view_definer,
            self.parent.cho_view_sql_security,
            self.parent.lbl_view_sql_security,
            self.parent.rad_view_algorithm_undefined,
            self.parent.rad_view_algorithm_merge,
            self.parent.rad_view_algorithm_temptable,
            self.parent.rad_view_constraint_local,
            self.parent.rad_view_constraint_cascaded,
            self.parent.chk_view_security_barrier,
        ]
        self._batch_show_hide(widgets_to_show, widgets_to_hide)
        self._normalize_radio_selection_constraint()

    def _apply_sqlite_visibility(self):
        widgets_to_hide = [
            self.parent.cho_view_schema,
            self.parent.lbl_view_schema,
            self.parent.cmb_view_definer,
            self.parent.lbl_view_definer,
            self.parent.cho_view_sql_security,
            self.parent.lbl_view_sql_security,
            self.parent.rad_view_algorithm_undefined,
            self.parent.rad_view_algorithm_merge,
            self.parent.rad_view_algorithm_temptable,
            self.parent.rad_view_constraint_none,
            self.parent.rad_view_constraint_local,
            self.parent.rad_view_constraint_cascaded,
            self.parent.rad_view_constraint_check_only,
            self.parent.rad_view_constraint_read_only,
            self.parent.chk_view_security_barrier,
            self.parent.chk_view_force,
        ]
        self._batch_show_hide([], widgets_to_hide)

    def _batch_show_hide(self, show: list[wx.Window], hide: list[wx.Window]):
        for widget in show:
            widget.Show(True)
        for widget in hide:
            widget.Show(False)

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

