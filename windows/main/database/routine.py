import dataclasses
from typing import Optional

import wx
import wx.dataview

from gettext import gettext as _

from helpers.bindings import AbstractModel, wx_call_after_debounce
from helpers.dataview import BaseDataViewListModel, ColumnField
from helpers.logger import logger
from helpers.observables import Observable

from structures.connection import ConnectionEngine
from structures.engines.database import SQLFunction, SQLProcedure

from windows.main import (
    CURRENT_DATABASE,
    CURRENT_FUNCTION,
    CURRENT_PROCEDURE,
    CURRENT_SESSION,
)


@dataclasses.dataclass
class RoutineParameter:
    index: int = 0
    name: str = ""
    datatype: str = ""
    context: str = "IN"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RoutineParameter):
            return False
        return (
            self.index == other.index
            and self.name == other.name
            and self.datatype == other.datatype
            and self.context == other.context
        )

    def copy(self) -> "RoutineParameter":
        return RoutineParameter(
            index=self.index,
            name=self.name,
            datatype=self.datatype,
            context=self.context,
        )


class RoutineParametersModel(BaseDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("index"),
        1: ColumnField("name"),
        2: ColumnField("datatype"),
        3: ColumnField("context"),
    }

    def __init__(self) -> None:
        super().__init__(column_count=4)
        self._parameters: list[RoutineParameter] = []

    def load_parameters(self, parameters: list[RoutineParameter]) -> None:
        self._parameters = [p.copy() for p in parameters]
        self.Reset(len(self._parameters))

    def get_data_by_row(self, row: int) -> RoutineParameter:
        return self._parameters[row]

    def set_data_by_row(self, row: int, data: RoutineParameter) -> None:
        self._parameters[row] = data

    @property
    def parameters(self) -> list[RoutineParameter]:
        return self._parameters

    def insert_parameter(self, index: int, parameter: RoutineParameter) -> None:
        self._parameters.insert(index, parameter)
        self._reindex()
        self.Reset(len(self._parameters))

    def remove_parameter(self, parameter: RoutineParameter) -> None:
        self._parameters.remove(parameter)
        self._reindex()
        self.Reset(len(self._parameters))

    def clear_parameters(self) -> None:
        self._parameters = []
        self.Reset(0)

    def _reindex(self) -> None:
        for i, param in enumerate(self._parameters):
            param.index = i


class RoutineModel(AbstractModel):
    def __init__(self) -> None:
        super().__init__()

        self.routine_name = Observable()
        self.routine_schema = Observable()
        self.routine_type = Observable()
        self.routine_return_type = Observable()
        self.routine_comment = Observable()
        self.routine_language = Observable()
        self.routine_body = Observable()

        self.behavior_data_access = Observable()
        self.behavior_deterministic = Observable()
        self.behavior_volatility = Observable()
        self.behavior_parallel = Observable()
        self.behavior_cost = Observable()
        self.behavior_rows = Observable()

        self.security_definer = Observable()
        self.security_sql_security = Observable()

        self.parameters_model = RoutineParametersModel()

        wx_call_after_debounce(
            self.routine_name,
            self.routine_schema,
            self.routine_type,
            self.routine_return_type,
            self.routine_comment,
            self.routine_language,
            self.routine_body,
            self.behavior_data_access,
            self.behavior_deterministic,
            self.behavior_volatility,
            self.behavior_parallel,
            self.behavior_cost,
            self.behavior_rows,
            self.security_definer,
            self.security_sql_security,
            callback=self._on_model_changed,
        )

        CURRENT_PROCEDURE.subscribe(self._on_current_procedure_changed)
        CURRENT_FUNCTION.subscribe(self._on_current_function_changed)

    def _on_model_changed(self, *args) -> None:
        pass

    def _on_current_procedure_changed(
        self, procedure: Optional[SQLProcedure]
    ) -> None:
        if procedure is None:
            return
        self._load_routine(procedure, is_function=False)

    def _on_current_function_changed(
        self, function: Optional[SQLFunction]
    ) -> None:
        if function is None:
            return
        self._load_routine(function, is_function=True)

    def _load_routine(
        self, routine: SQLFunction | SQLProcedure, is_function: bool
    ) -> None:
        self.routine_name.set_initial(routine.name)
        self.routine_type.set_initial(
            "FUNCTION" if is_function else "PROCEDURE"
        )

        if is_function:
            self.routine_return_type.set_initial(
                getattr(routine, "returns", "")
            )
        else:
            self.routine_return_type.set_initial("")

        self.routine_body.set_initial(getattr(routine, "statement", ""))
        self.routine_comment.set_initial(getattr(routine, "comment", ""))

        parameters_text = getattr(routine, "parameters", "")
        parameters = self._parse_parameters(parameters_text)
        self.parameters_model.load_parameters(parameters)

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        engine = session.engine
        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._load_mysql_fields(routine)
        elif engine == ConnectionEngine.POSTGRESQL:
            self._load_postgresql_fields(routine)

    def _load_mysql_fields(self, routine: SQLFunction | SQLProcedure) -> None:
        if hasattr(routine, "definer"):
            self.security_definer.set_initial(getattr(routine, "definer", ""))
        if hasattr(routine, "deterministic"):
            self.behavior_deterministic.set_initial(
                getattr(routine, "deterministic", False)
            )
        if hasattr(routine, "data_access"):
            self.behavior_data_access.set_initial(
                getattr(routine, "data_access", "")
            )

    def _load_postgresql_fields(
        self, routine: SQLFunction | SQLProcedure
    ) -> None:
        if hasattr(routine, "language"):
            self.routine_language.set_initial(
                getattr(routine, "language", "plpgsql")
            )
        if hasattr(routine, "volatility"):
            self.behavior_volatility.set_initial(
                getattr(routine, "volatility", "VOLATILE")
            )

    def _parse_parameters(self, parameters_text: str) -> list[RoutineParameter]:
        if not parameters_text or not parameters_text.strip():
            return []

        parameters: list[RoutineParameter] = []
        for idx, param_str in enumerate(parameters_text.split(",")):
            param_str = param_str.strip()
            if not param_str:
                continue

            parts = param_str.split()
            name = ""
            datatype = ""
            context = "IN"

            if len(parts) >= 3:
                context = parts[0].upper()
                name = parts[1]
                datatype = " ".join(parts[2:])
            elif len(parts) == 2:
                name = parts[0]
                datatype = parts[1]
            elif len(parts) == 1:
                datatype = parts[0]

            parameters.append(
                RoutineParameter(
                    index=idx,
                    name=name,
                    datatype=datatype,
                    context=context if context in ("IN", "OUT", "INOUT") else "IN",
                )
            )

        return parameters

    def format_parameters(self) -> str:
        parts: list[str] = []
        for param in self.parameters_model.parameters:
            if param.name and param.datatype:
                parts.append(f"{param.context} {param.name} {param.datatype}")
            elif param.datatype:
                parts.append(param.datatype)
        return ", ".join(parts)

    def sync_to_routine(
        self, routine: SQLFunction | SQLProcedure, is_function: bool
    ) -> None:
        routine.name = self.routine_name.get_value() or routine.name
        if hasattr(routine, "parameters"):
            routine.parameters = self.format_parameters()
        if hasattr(routine, "statement"):
            routine.statement = self.routine_body.get_value() or ""
        if hasattr(routine, "comment"):
            routine.comment = self.routine_comment.get_value() or ""

        if is_function and hasattr(routine, "returns"):
            routine.returns = self.routine_return_type.get_value() or ""

        session = CURRENT_SESSION.get_value()
        if not session:
            return

        engine = session.engine
        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._sync_mysql_fields(routine)
        elif engine == ConnectionEngine.POSTGRESQL:
            self._sync_postgresql_fields(routine)

    def _sync_mysql_fields(self, routine: SQLFunction | SQLProcedure) -> None:
        if hasattr(routine, "definer"):
            routine.definer = self.security_definer.get_value() or ""
        if hasattr(routine, "deterministic"):
            routine.deterministic = self.behavior_deterministic.get_value() or False

    def _sync_postgresql_fields(
        self, routine: SQLFunction | SQLProcedure
    ) -> None:
        if hasattr(routine, "language"):
            routine.language = self.routine_language.get_value() or "plpgsql"
        if hasattr(routine, "volatility"):
            routine.volatility = (
                self.behavior_volatility.get_value() or "VOLATILE"
            )


class RoutineController:
    def __init__(self, parent) -> None:
        self.parent = parent

        try:
            from windows.components.stc.styles import apply_stc_theme
            from windows.components.stc.profiles import SQL

            apply_stc_theme(self.parent.routine_stc)
            SQL.apply(self.parent.routine_stc)
        except Exception:
            pass

        self.model = RoutineModel()
        self._bind_controls()
        self._bind_parameter_tools()
        self._bind_type_change()

        wx_call_after_debounce(
            self.model.routine_name,
            self.model.routine_type,
            self.model.routine_return_type,
            self.model.routine_comment,
            self.model.routine_language,
            self.model.routine_body,
            self.model.behavior_data_access,
            self.model.behavior_deterministic,
            self.model.behavior_volatility,
            self.model.behavior_parallel,
            self.model.behavior_cost,
            self.model.behavior_rows,
            self.model.security_definer,
            self.model.security_sql_security,
            callback=self._update_button_states,
        )

        CURRENT_PROCEDURE.subscribe(self._on_routine_changed)
        CURRENT_FUNCTION.subscribe(self._on_routine_changed)

    def _bind_controls(self) -> None:
        self.model.bind_controls(
            routine_name=self.parent.routine_name,
            routine_body=self.parent.routine_stc,
            security_definer=self.parent.routine_definer,
        )

    def _bind_parameter_tools(self) -> None:
        self.parent.routine_parameters.AssociateModel(self.model.parameters_model)

    def _bind_type_change(self) -> None:
        self.parent.routine_type.Bind(wx.EVT_CHOICE, self.on_type_changed)

    def _get_current_routine(
        self,
    ) -> Optional[SQLFunction | SQLProcedure]:
        proc = CURRENT_PROCEDURE.get_value()
        if proc is not None:
            return proc
        func = CURRENT_FUNCTION.get_value()
        if func is not None:
            return func
        return None

    def _is_function(self) -> bool:
        routine = self._get_current_routine()
        if routine is None:
            return False
        return isinstance(routine, SQLFunction)

    def _is_procedure(self) -> bool:
        routine = self._get_current_routine()
        if routine is None:
            return False
        return isinstance(routine, SQLProcedure)

    def _has_changes(self) -> bool:
        routine = self._get_current_routine()
        if routine is None:
            return False
        if routine.is_new:
            return True

        name = self.model.routine_name.get_value()
        body = self.model.routine_body.get_value()
        params = self.model.format_parameters()

        if name and name != routine.name:
            return True
        if body and body != getattr(routine, "statement", ""):
            return True
        if params != getattr(routine, "parameters", ""):
            return True

        return False

    def _update_button_states(self, *args, **kwargs) -> None:
        routine = self._get_current_routine()
        if routine is None:
            self.parent.btn_routine_save.Enable(False)
            self.parent.btn_routine_cancel.Enable(False)
            self.parent.btn_routine_delete.Enable(False)
            return

        has_changes = self._has_changes()
        self.parent.btn_routine_save.Enable(has_changes)
        self.parent.btn_routine_cancel.Enable(has_changes)
        self.parent.btn_routine_delete.Enable(not routine.is_new)

    def _on_routine_changed(
        self, routine: Optional[SQLFunction | SQLProcedure]
    ) -> None:
        self._update_button_states()

        if routine is None:
            return

        session = CURRENT_SESSION.get_value()
        if session:
            engine = session.engine
            self._apply_engine_visibility(engine)
            self._populate_definers(engine, session)

    def _populate_definers(
        self, engine: ConnectionEngine, session
    ) -> None:
        if engine not in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            return
        cmb = self.parent.routine_definer
        try:
            definers = session.context.get_definers()
            cmb.Clear()
            for definer in definers:
                cmb.Append(definer)

            current_definer = self.model.security_definer.get_value() or ""
            if current_definer:
                idx = cmb.FindString(current_definer)
                if idx == wx.NOT_FOUND:
                    cmb.Append(current_definer)
                    idx = cmb.FindString(current_definer)
                cmb.SetSelection(idx)
            elif cmb.GetCount() > 0:
                cmb.SetSelection(0)
        except Exception:
            pass

    def _apply_engine_visibility(self, engine: ConnectionEngine) -> None:
        mysql_panel = self.parent.panel_behavior_mysql_mariadb
        pg_panel = self.parent.panel_behavior_postgresql
        definer_panel = self.parent.routine_definer_panel
        sql_security_panel = self.parent.routine_security_panel

        if engine in (ConnectionEngine.MYSQL, ConnectionEngine.MARIADB):
            self._batch_show_hide(
                show=[mysql_panel, definer_panel, sql_security_panel],
                hide=[pg_panel],
            )
        elif engine == ConnectionEngine.POSTGRESQL:
            self._batch_show_hide(
                show=[pg_panel],
                hide=[mysql_panel, definer_panel, sql_security_panel],
            )
        else:
            self._batch_show_hide(
                show=[],
                hide=[mysql_panel, pg_panel, definer_panel, sql_security_panel],
            )

        self.parent.m_panel73.GetSizer().Layout()
        self.parent.panel_routine.Layout()

    def _batch_show_hide(
        self, show: list[wx.Window], hide: list[wx.Window]
    ) -> None:
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

    def on_type_changed(self, event: wx.CommandEvent) -> None:
        type_selection = self.parent.routine_type.GetStringSelection()
        is_function = "Function" in type_selection or "function" in type_selection.lower()
        self.parent.routine_return_type.Enable(is_function)
        if not is_function:
            self.parent.routine_return_type.SetSelection(wx.NOT_FOUND)

    def on_parameter_insert(self, event: wx.Event) -> None:
        selected = self.parent.routine_parameters.GetSelection()
        idx = len(self.model.parameters_model.parameters)
        if selected.IsOk():
            row = self.model.parameters_model.GetRow(selected)
            idx = row + 1

        new_param = RoutineParameter(
            index=idx,
            name="",
            datatype="",
            context="IN",
        )
        self.model.parameters_model.insert_parameter(idx, new_param)

    def on_parameter_remove(self, event: wx.Event) -> None:
        selected = self.parent.routine_parameters.GetSelection()
        if not selected.IsOk():
            return
        row = self.model.parameters_model.GetRow(selected)
        param = self.model.parameters_model.get_data_by_row(row)
        self.model.parameters_model.remove_parameter(param)

    def on_parameter_clear(self, event: wx.Event) -> None:
        self.model.parameters_model.clear_parameters()

    def on_save(self, event: wx.Event) -> None:
        self.do_save()

    def on_delete(self, event: wx.Event) -> None:
        self.do_delete()

    def on_cancel(self, event: wx.Event) -> None:
        self.do_cancel()

    def do_save(self) -> None:
        routine = self._get_current_routine()
        if not routine:
            return
        session = CURRENT_SESSION.get_value()
        if not session:
            return

        is_function = isinstance(routine, SQLFunction)
        is_new = routine.is_new

        try:
            self.model.sync_to_routine(routine, is_function)
            routine.save()

            if is_function:
                message = (
                    _("Function created successfully")
                    if is_new
                    else _("Function updated successfully")
                )
            else:
                message = (
                    _("Procedure created successfully")
                    if is_new
                    else _("Procedure updated successfully")
                )

            wx.MessageBox(message, _("Success"), wx.OK | wx.ICON_INFORMATION)
            self.parent.controller_tree_connections.refresh_current_database()

            if is_new:
                database = CURRENT_DATABASE.get_value()
                if is_function:
                    saved = next(
                        (
                            f
                            for f in database.functions
                            if f.name == routine.name
                        ),
                        None,
                    )
                    if saved:
                        CURRENT_FUNCTION.set_value(None)
                        CURRENT_FUNCTION.set_value(saved)
                else:
                    saved = next(
                        (
                            p
                            for p in database.procedures
                            if p.name == routine.name
                        ),
                        None,
                    )
                    if saved:
                        CURRENT_PROCEDURE.set_value(None)
                        CURRENT_PROCEDURE.set_value(saved)
                return

            self._update_button_states()
        except Exception as e:
            wx.MessageBox(
                _("Error saving routine: {}").format(str(e)),
                _("Error"),
                wx.OK | wx.ICON_ERROR,
            )

    def do_delete(self) -> None:
        routine = self._get_current_routine()
        if not routine:
            return
        session = CURRENT_SESSION.get_value()
        if not session:
            return

        is_function = isinstance(routine, SQLFunction)
        type_label = _("Function") if is_function else _("Procedure")

        result = wx.MessageBox(
            _("Are you sure you want to delete {} '{}'?").format(
                type_label, routine.name
            ),
            _("Confirm Delete"),
            wx.YES_NO | wx.ICON_QUESTION,
        )
        if result != wx.YES:
            return

        try:
            routine.drop()
            wx.MessageBox(
                _("{} deleted successfully").format(type_label),
                _("Success"),
                wx.OK | wx.ICON_INFORMATION,
            )

            database = CURRENT_DATABASE.get_value()
            if is_function:
                CURRENT_FUNCTION.set_value(None)
                database.functions.refresh()
            else:
                CURRENT_PROCEDURE.set_value(None)
                database.procedures.refresh()
            self.parent.controller_tree_connections.refresh_current_database()
        except Exception as e:
            wx.MessageBox(
                _("Error deleting routine: {}").format(str(e)),
                _("Error"),
                wx.OK | wx.ICON_ERROR,
            )

    def do_cancel(self) -> None:
        routine = self._get_current_routine()
        if not routine:
            return

        is_function = isinstance(routine, SQLFunction)
        if is_function:
            CURRENT_FUNCTION.set_value(None)
            CURRENT_FUNCTION.set_value(routine)
        else:
            CURRENT_PROCEDURE.set_value(None)
            CURRENT_PROCEDURE.set_value(routine)
        self._update_button_states()
