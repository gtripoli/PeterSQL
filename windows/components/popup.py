import datetime
from typing import List, Self, Any, Dict, Optional

import wx
import wx.adv

from gettext import gettext as _

from windows.main import CURRENT_SESSION

from engines.session import Session
from engines.structures.datatype import SQLDataType, DataTypeCategory, StandardDataType


class BasePopup(wx.PopupTransientWindow):
    popup_size: wx.Size
    column_width: int = 100
    default_value: Optional[str] = None

    def __init__(self, parent):
        super().__init__(parent, flags=wx.BORDER_NONE)
        self._value = None
        self._initial = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetWindowStyle(wx.TRANSPARENT_WINDOW)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetSizer(self.sizer)

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

        return self

    def get_initial(self):
        return self._initial

    def open(self, value: Any, position: wx.Point) -> Self:
        self._value = value
        self._initial = value

        self.SetPosition(position)
        self.SetMinSize(self.popup_size)
        self.SetMaxSize(self.popup_size)

        self.Layout()
        self.sizer.Fit(self)
        self.Fit()

        wx.CallAfter(self.Popup)

        return self

    def Dismiss(self):
        if hasattr(self, 'OnDismiss') and self.OnDismiss:
            self.OnDismiss()
        super().Dismiss()


class PopupColumnDefault(BasePopup):
    default_value: str = "No default"

    def __init__(self, parent):
        super().__init__(parent)

        self.rb_no_default = wx.RadioButton(self, wx.ID_ANY, _(u"No default value"), wx.DefaultPosition, wx.DefaultSize,
                                            0)
        self.rb_no_default.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_no_default, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_null = wx.RadioButton(self, wx.ID_ANY, _(u"NULL"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rb_null.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_null, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_auto_increment = wx.RadioButton(self, wx.ID_ANY, _(u"AUTO INCREMENT"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rb_auto_increment.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_auto_increment, 0, wx.ALL | wx.EXPAND, 5)

        self.rb_expression = wx.RadioButton(self, wx.ID_ANY, _(u"Text/Expression"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rb_expression.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button)
        self.sizer.Add(self.rb_expression, 0, wx.ALL | wx.EXPAND, 5)

        self.txt_expression = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE)
        self.txt_expression.Enable(False)
        self.txt_expression.Bind(wx.EVT_TEXT, self._on_expression_changed)
        self.sizer.Add(self.txt_expression, 0, wx.ALL | wx.EXPAND, 5)

    def _on_radio_button(self, event):
        self.txt_expression.Enable(False)

        if self.rb_no_default.GetValue():
            self._value = None
        elif self.rb_null.GetValue():
            self._value = "NULL"
        elif self.rb_auto_increment.GetValue():
            self._value = "AUTO_INCREMENT"
        elif self.rb_expression.GetValue():
            self._value = ""
            self.txt_expression.Enable(True)
            # self.txt_expression.SetFocus()

    def _on_expression_changed(self, event):
        if self.rb_expression.GetValue():
            self._value = self.txt_expression.GetValue()

    def on_key_arrow_down(self, event):
        if self.rb_no_default.HasFocus():
            self.rb_expression.SetFocus()
        elif self.rb_expression.HasFocus():
            self.rb_null.SetFocus()
        elif self.rb_null.HasFocus():
            self.rb_auto_increment.SetFocus()

        print(self.rb_no_default.HasFocus(), self.rb_expression.HasFocus(), self.rb_null.HasFocus(), self.rb_auto_increment.HasFocus())
        # elif self.rb_auto_increment.HasFocus() :
        #     self.rb_no_default.SetFocus()

        return event.Skip()

    def on_key_arrow_up(self, event):
        # if self.rb_no_default.HasFocus() :
        #     self.rb_auto_increment.SetFocus()

        if self.rb_auto_increment.HasFocus():
            self.rb_null.SetFocus()
        elif self.rb_null.HasFocus():
            self.rb_expression.SetFocus()
        elif self.rb_expression.HasFocus():
            self.rb_no_default.SetFocus()

        return event.Skip()

    def set_value(self, value):
        """Set the initial value and update UI accordingly."""
        super().set_value(value)

        if not value:
            self.rb_no_default.SetValue(True)
        elif value == "NULL":
            self.rb_null.SetValue(True)
        elif value == "AUTO_INCREMENT":
            self.rb_auto_increment.SetValue(True)
        else:
            self.rb_expression.SetValue(True)
            self.txt_expression.Enable(True)
            self.txt_expression.SetValue(value)
            self.txt_expression.SetFocus()

        return self

    def open(self, value: Any, position: wx.Point) -> Self:
        self.set_value(value)

        return super().open(value, position)


class PopupColumnDatatype(BasePopup):
    session: Session
    choices_groups: Dict[DataTypeCategory, List[str]] = {}

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.tree_ctrl = None

        self.tree_ctrl = wx.TreeCtrl(self, style=wx.TR_HIDE_ROOT | wx.TR_NO_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT |
                                                 wx.TR_NO_LINES | wx.TR_SINGLE)

        self.tree_ctrl.AddRoot("Root")

        self.sizer.Add(self.tree_ctrl, 1, wx.ALL | wx.EXPAND, 0)

        self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_active)
        self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_COLLAPSING, lambda e: e.Veto())

        self.session = CURRENT_SESSION.get_value()
        self.set_choices(self.session.datatype.get_all())

        # CURRENT_SESSION.subscribe(self._load_session, execute_immediately=True)

    # def _load_session(self, session: Session):


    def _on_active(self, event):
        item = event.GetItem()
        root = self.tree_ctrl.GetRootItem()
        if item and item != root:
            if self.tree_ctrl.GetItemParent(item) != root:
                self._value = self.tree_ctrl.GetItemText(item)

                self.Dismiss()

        event.Skip()

    def set_choices(self, choices: List[SQLDataType]) -> Self:
        dc = wx.ClientDC(self.tree_ctrl)
        popup_width: int = 0
        groups: Dict[DataTypeCategory, List[str]] = {}

        for choice in choices:
            choice_width, choice_h = dc.GetTextExtent(choice.name)
            category_width, category_h = dc.GetTextExtent(choice.category.value.name)

            popup_width = max(popup_width, choice_width, category_width)
            groups.setdefault(choice.category, []).append(choice.name)

        self.choices_groups = groups
        self.popup_size = wx.Size(popup_width + 100, 300)

        return self

    def get_value(self):
        return self.session.datatype.get_by_name(self._value)

    def open(self, value: Any, position: wx.Point) -> Self:

        root = self.tree_ctrl.GetRootItem()
        self.tree_ctrl.DeleteChildren(root)

        selected = None

        for category, datatypes in self.choices_groups.items():

            category_item = self.tree_ctrl.AppendItem(root, category.value.name)
            self.tree_ctrl.SetItemBold(category_item, True)

            for datatype in datatypes:
                datatype_item = self.tree_ctrl.AppendItem(category_item, datatype)
                self.tree_ctrl.SetItemTextColour(datatype_item, category.value.color)

                if datatype == value:
                    selected = datatype_item

        self.tree_ctrl.ExpandAll()

        if selected is not None:
            self.tree_ctrl.SelectItem(selected)
            self.tree_ctrl.EnsureVisible(selected)

        return super().open(value, position)


class PopupCheckList(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.choices = []
        self.check_list_box = wx.CheckListBox(self)
        self.sizer.Add(self.check_list_box, 0, wx.ALL | wx.EXPAND, 5)
        self.check_list_box.Bind(wx.EVT_CHECKLISTBOX, self._on_select)

    def set_choices(self, choices: List[str]) -> Self:
        self.choices = choices

        dc = wx.ClientDC(self.check_list_box)
        popup_width = 0
        for choice in self.choices:
            popup_width = max(popup_width, dc.GetTextExtent(choice)[0])

        self.popup_size = wx.Size(popup_width + 100, -1)

    def open(self, value: str, position: wx.Point) -> Self:
        self.check_list_box.AppendItems(self.choices)

        super().open(value, position)

        if value := self.get_value():
            self.check_list_box.SetCheckedStrings(value.split(','))

        if self.check_list_box.GetCount() > 0:
            self.check_list_box.SetSelection(0)

        wx.CallAfter(self.SetFocus)

        return self

    def _on_select(self, event):
        self._value = ",".join(self.check_list_box.GetCheckedStrings())
        event.Skip()

        return self


class PopupChoice(BasePopup):
    def __init__(self, parent):
        super().__init__(parent)
        self.choices = []
        self.choice = wx.Choice(self)
        self.sizer.Add(self.choice, 0, wx.ALL | wx.EXPAND, 0)
        self.choice.Bind(wx.EVT_CHOICE, self._on_select)

    def _on_select(self, event):
        self._value = self.choice.GetStringSelection()
        event.Skip()

        return self

    def set_choices(self, choices: List[str]):
        self.choices = choices
        # self.choice.SetItems(choices)

    def open(self, value: str, position: wx.Point) -> Self:
        self.choice.AppendItems(self.choices)

        position.y -= int((self.choice.GetSize().GetHeight() / 4))

        super().open(value, position)

        if value := self.get_value():
            self.choice.SetStringSelection(value)


class PopupCalendar(BasePopup):
    popup_size = wx.Size(-1, -1)

    def __init__(self, parent):
        super().__init__(parent)
        self.calendar_picker = wx.adv.CalendarCtrl(self, style=wx.adv.CAL_SHOW_WEEK_NUMBERS)
        self.sizer.Add(self.calendar_picker, 0, wx.ALL | wx.CENTER, 5)
        self.calendar_picker.Bind(wx.adv.EVT_CALENDAR, self._on_calendar)

    def _on_calendar(self, event):
        date = self.calendar_picker.GetDate()
        self._value = date.FormatISODate()
        self.Dismiss()
        event.Skip()

    def set_value(self, value):
        super().set_value(value)
        if value:
            try:
                dt = wx.DateTime()
                dt.ParseISODate(value)
                self.calendar_picker.SetDate(dt)
            except:
                pass
        return self

    def open(self, value: str, position: wx.Point) -> Self:
        self.set_value(value)
        return super().open(value, position)


class PopupTime(BasePopup):
    popup_size = wx.Size(200, 100)

    def __init__(self, parent):
        super().__init__(parent)
        self.time_picker = wx.TimePickerCtrl(self)
        self.sizer.Add(self.time_picker, 0, wx.ALL | wx.CENTER, 5)
        self.time_picker.Bind(wx.EVT_TIME_CHANGED, self._on_time_changed)

    def _on_time_changed(self, event):
        time = self.time_picker.GetValue()
        self._value = time.FormatISOTime()
        event.Skip()

    def set_value(self, value):
        super().set_value(value)
        if value:
            try:
                dt = wx.DateTime()
                dt.ParseISOTime(value)
                self.time_picker.SetValue(dt)
            except:
                pass
        return self

    def open(self, value: str, position: wx.Point) -> Self:
        self.set_value(value)
        return super().open(value, position)


class PopupCalendarTime(BasePopup):
    popup_size = wx.Size(-1, -1)

    _date: str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    _time: str = datetime.datetime.now(datetime.UTC).strftime("%H:%M:%S")

    def __init__(self, parent):
        super().__init__(parent)
        self.calendar_picker = wx.adv.CalendarCtrl(self, style=wx.adv.CAL_SHOW_WEEK_NUMBERS)
        self.sizer.Add(self.calendar_picker, 0, wx.ALL | wx.CENTER, 5)

        self.time_picker = wx.adv.TimePickerCtrl(self, style=wx.adv.TP_DEFAULT)
        self.sizer.Add(self.time_picker, 0, wx.ALL | wx.EXPAND | wx.CENTER, 5)

        self.calendar_picker.Bind(wx.adv.EVT_CALENDAR_SEL_CHANGED, self._on_calendar_changed)
        self.time_picker.Bind(wx.adv.EVT_TIME_CHANGED, self._on_time_changed)

    def _on_calendar_changed(self, event):
        date = self.calendar_picker.GetDate()
        self._date = date.FormatISODate()
        event.Skip()

    def _on_time_changed(self, event):
        time = self.time_picker.GetValue()
        self._time = time.FormatISOTime()
        event.Skip()

    def set_value(self, value):
        super().set_value(value)
        if value:
            self._date, self._time = value.split(" ")
            try:
                dt = wx.DateTime()
                dt.ParseISODate(self._date)
                self.calendar_picker.SetDate(dt)

                dt.ParseISOTime(self._time)
                self.time_picker.SetValue(dt)
            except:
                pass
        return self

    def get_value(self):
        return f"{self._date} {self._time}"

    def open(self, value: str, position: wx.Point) -> Self:
        self.set_value(value)
        return super().open(value, position)
    #
    # def Dismiss(self):
    #
    #     super().Dismiss()


#
# class PopupDateTime(BasePopup):
#     popup_size = wx.Size(250, 150)
#
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.date_picker = wx.DatePickerCtrl(self, style=wx.DP_DEFAULT | wx.DP_SHOWCENTURY)
#         self.time_picker = wx.TimePickerCtrl(self)
#         self.sizer.Add(self.date_picker, 0, wx.ALL | wx.EXPAND, 5)
#         self.sizer.Add(self.time_picker, 0, wx.ALL | wx.EXPAND, 5)
#         self.date_picker.Bind(wx.EVT_DATE_CHANGED, self._on_changed)
#         self.time_picker.Bind(wx.EVT_TIME_CHANGED, self._on_changed)
#
#     def _on_changed(self, event):
#         date = self.date_picker.GetValue()
#         time = self.time_picker.GetValue()
#         self._value = f"{date.FormatISODate()} {time.FormatISOTime()}"
#         event.Skip()
#
#     def set_value(self, value):
#         super().set_value(value)
#         if value:
#             try:
#                 parts = value.split(' ')
#                 if len(parts) == 2:
#                     date_str, time_str = parts
#                     dt_date = wx.DateTime()
#                     dt_date.ParseISODate(date_str)
#                     self.date_picker.SetValue(dt_date)
#                     dt_time = wx.DateTime()
#                     dt_time.ParseISOTime(time_str)
#                     self.time_picker.SetValue(dt_time)
#             except:
#                 pass
#         return self
#
#     def open(self, value: str, position: wx.Point) -> Self:
#         self.set_value(value)
#         return super().open(value, position)
#
# #
# class ForeignKeyChoices(BasePopup):
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.choices = []
#         self.choice = wx.Choice(self)
#         self.sizer.Add(self.choice, 0, wx.ALL | wx.EXPAND, 0)
#         self.choice.Bind(wx.EVT_CHOICE, self._on_select)
#
#     def _on_select(self, event):
#         self._value = self.choice.GetStringSelection()
#         event.Skip()
#
#         return self
#
#     def set_choices(self, choices: List[str]):
#         self.choices = choices
#
#     def open(self, value: str, position: wx.Point) -> Self:
#         self.choice.AppendItems(self.choices)
#
#         position.y -= int((self.choice.GetSize().GetHeight() / 4))
#
#         super().open(value, position)
#
#         if value := self.get_value():
#             self.choice.SetStringSelection(value)
#
#         wx.CallAfter(self.SetFocus)
#
#         return self
#
#
# # class ForeignKeyRenderer(BasePopup):
# #     def __init__(self, foreign_key: SQLForeignKey):
# #         super().__init__(mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
# #         self.foreign_key = foreign_key
# #         self.choices = []
# #
# #     def HasEditorCtrl(self):
# #         return True
# #
# #     def CreateEditorCtrl(self, parent, rect, value):
# #         session = CURRENT_SESSION.get_value()
# #         database = CURRENT_DATABASE.get_value()
# #
# #         records = session.context.get_records(
# #             next((table for table in database.tables if table.name == self.foreign_key.reference_table), None)
# #         )
# #
# #         references = []
# #         for record in records:
# #             reference = [str(getattr(record, reference_column)) for reference_column in self.foreign_key.reference_columns]
# #             if hasattr(record, "name"):
# #                 reference.append(getattr(record, "name"))
# #
# #             references.append(reference)
# #
# #         choices = [
# #             f" ".join(reference) for reference in references
# #         ]
# #
# #         choice = wx.Choice(parent, choices=choices)
# #         choice.SetSize(rect.GetSize())
# #         return choice
