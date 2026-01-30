import wx
import wx.adv
import wx.dataview

from typing import Type, Optional, Callable

from windows.components import BaseDataViewCustomRenderer, BaseTextRenderer, Validator, TextCtrlWithDialogButton
from windows.components.popup import BasePopup


class PopupRenderer(BaseDataViewCustomRenderer):
    def __init__(self, popup_class: Type[BasePopup], on_open: Optional[Callable[[BasePopup], None]] = None):
        super().__init__("string", mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE)

        self._value = ""
        self._popup: Optional[BasePopup] = None

        self.popup_class: Type[BasePopup] = popup_class
        self.on_open: Optional[Callable[[BasePopup], None]] = on_open

    def GetSize(self):
        view = self.GetView()
        value = self._value.strip() or getattr(self.popup_class, "default_value", "")

        if not value:
            return wx.Size(50, view.CharHeight)

        dc = wx.ClientDC(view)
        w, h = dc.GetTextExtent(value)[0], view.CharHeight + dc.GetTextExtent(" ")[0]

        return wx.Size(w + 50, h)

    def Render(self, rect, dc, state):
        return super().Render(rect, dc, state, getattr(self.popup_class, "default_value", ""))

    def ActivateCell(self, rect, model, item, col, mouseEvent):
        view = self.GetView()

        x_scroll_offset = view.GetItemRect(item).left

        position = view.ClientToScreen(wx.Point(rect.x + x_scroll_offset, int(rect.y + view.CharHeight + (view.CharHeight / 2))))

        self._popup = self.popup_class(view)
        if not hasattr(self._popup, "popup_size"):
            self._popup.popup_size = wx.Size(view.GetColumn(col).GetWidth(), -1)

        def _on_dismiss():
            if self._popup is not None:
                if str((new_value := self._popup.get_value())) != self._value:
                    self._value = new_value
                    model.SetValue(self._value, item, col)
            else:
                raise ValueError("Popup is None")

            return True

        if self.on_open:
            self.on_open(self._popup)

        self._popup.open(self._value, position)
        self._popup.on_dismiss = _on_dismiss

        return True

    def CancelEditing(self):
        if self._popup is not None:
            self._popup.Dismiss()
            self._popup = None

        return True

    def FinishEditing(self):
        if self._popup is not None:
            self._popup.Dismiss()
            self._popup.Close()
            self._popup = None

        return True


class LengthSetRender(BaseTextRenderer):
    pass


class TextRenderer(BaseTextRenderer):
    pass


class AdvancedTextRenderer(BaseTextRenderer):
    def __init__(self, varianttype="string",
                 mode=wx.dataview.DATAVIEW_CELL_EDITABLE,
                 align=wx.ALIGN_LEFT,
                 validators=None,
                 dialog_factory=None):
        super().__init__(varianttype=varianttype, mode=mode, align=align, validators=validators)

        # funzione che crea il dialog (così la tieni separata)
        self.dialog_factory = dialog_factory

    def CreateEditorCtrl(self, parent, rect, value):
        initial = str(value or "")

        def open_dialog(panel: TextCtrlWithDialogButton):
            if not self.dialog_factory:
                return

            dlg = self.dialog_factory(parent, panel.GetValue())
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    panel.SetValue(dlg.get_value())
            finally:
                dlg.Destroy()

        editor = TextCtrlWithDialogButton(
            parent=parent,
            value=initial,
            on_open_dialog=open_dialog,
            validators=self.validators
        )

        # IMPORTANT: dimensiona il panel come il rect dell'editor
        editor.SetSize(rect.GetSize())
        editor.SetMinSize(rect.GetSize())

        return editor

    def GetValueFromEditorCtrl(self, editor):
        # editor qui è il panel restituito da CreateEditorCtrl
        return editor.GetValue()


class IntegerRenderer(BaseTextRenderer):
    def __init__(self, varianttype="string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT):
        validators = [
            Validator(self.validate)
        ]

        super().__init__(varianttype, mode, align, validators)

    def validate(self, event):
        unicode = event.GetUnicodeKey()

        if unicode > 0:
            return chr(unicode).isdigit()
        else:
            return event.GetKeyCode() in [wx.WXK_DELETE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]


class FloatRenderer(TextRenderer):
    def __init__(self, varianttype="string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT):

        validators = [
            Validator(self.validate),
        ]

        super().__init__(varianttype, mode, align, validators)

    def HasEditorCtrl(self):
        return True

    def validate(self, event):
        unicode = event.GetUnicodeKey()

        if unicode > 0:
            return chr(unicode).isdigit() or chr(unicode) == '.'
        else:
            return event.GetKeyCode() in [wx.WXK_DELETE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]


class DateTimeRenderer(BaseDataViewCustomRenderer):
    def __init__(self):
        super().__init__(varianttype="datetime", mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE)

    def Render(self, rect, dc, state):
        """Render datetime value in locale format"""
        value = self.GetValue()
        if value:
            text = value.Format('%x %X')
            # dc.DrawText(text, rect.x, rect.y)

            self.RenderText(text, 0, rect, dc, state)

        return True

    def CreateEditorCtrl(self, parent, rect, value):
        """Create date and time picker control"""
        date_picker = wx.DatePickerCtrl(parent)
        time_picker = wx.TimePickerCtrl(parent)

        # Set current value if available
        if value:
            date_picker.SetValue(value)
            time_picker.SetTime(value)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(date_picker)
        sizer.Add(time_picker)

        panel = wx.Panel(parent)
        panel.SetSizer(sizer)
        panel.SetSize(rect.GetSize())

        return panel


class TimeRenderer(BaseDataViewCustomRenderer):
    def __init__(self):
        super().__init__(varianttype="string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE)

    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(self, parent, rect, value):
        """Create time picker control"""
        time_picker = wx.adv.TimePickerCtrl(parent, style=wx.adv.TP_DEFAULT)
        time_picker.SetSize(rect.GetSize())

        # Set current value if available
        if value:
            try:
                # Parse time string (HH:MM:SS)
                hours, minutes, seconds = map(int, value.split(':'))
                time_picker.SetTime(hours, minutes, seconds)
            except (ValueError, AttributeError):
                pass

        return time_picker

    def GetValueFromEditorCtrl(self, editor):
        """Get formatted time string"""
        hours, minutes, seconds = editor.GetTime()
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
