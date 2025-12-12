from typing import Any, Callable, List, Optional, Self

import wx
import wx.dataview

from helpers.logger import logger


class Validator:
    def __init__(self, validator: Callable[[Any], bool]):
        self.validator = validator


class BaseDataViewCustomRenderer(wx.dataview.DataViewCustomRenderer):
    def __init__(self, varianttype="string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT):
        super().__init__(varianttype=varianttype, mode=mode, align=align)

        self._value = None

    def SetValue(self, value):
        self._value = value
        return True

    def GetValue(self):
        return self._value

    def GetSize(self):
        view = self.GetView()

        dc = wx.ClientDC(view)

        char_width = 50
        if self._value is not None:
            char_width = dc.GetTextExtent(str(self._value)).GetWidth()

        size = wx.Size(char_width, view.CharHeight)
        # [0], view.CharHeight + dc.GetTextExtent(" ")[0] + 50

        size += (50, dc.GetTextExtent(" ")[0])

        return size

    def Render(self, rect, dc, state, default: str = ""):
        value = self.GetValue()

        if value and not str(value).strip() and str(default).strip():
            value = default

        # if (focused := state & wx.dataview.DATAVIEW_CELL_FOCUSED):
        #     old_pen, old_brush = dc.GetPen(), dc.GetBrush()
        #     highlight_rect = wx.Rect(rect)
        #     if highlight_rect.Width > 2 and highlight_rect.Height > 2:
        #         highlight_rect.Deflate(1, 1)
        #     dc.SetPen(wx.TRANSPARENT_PEN)
        #     dc.SetBrush(wx.Brush(wx.Colour(229, 244, 255)))
        #     dc.DrawRectangle(highlight_rect)
        #     dc.SetPen(wx.Pen(wx.Colour(66, 133, 244), width=2))
        #     dc.SetBrush(wx.TRANSPARENT_BRUSH)
        #     dc.DrawRoundedRectangle(highlight_rect, radius=3)
        #     dc.SetPen(old_pen)
        #     dc.SetBrush(old_brush)

        # if (focused := state & wx.dataview.DATAVIEW_CELL_FOCUSED):
        # dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), width=1))
        # dc.SetBrush(wx.TRANSPARENT_BRUSH)
        # dc.DrawRoundedRectangle(rect, radius=3)

        self.RenderText(str(value), 0, rect, dc, state)

        return True

    def RenderText(self, text, x, rect, dc, state):

        # w, h = dc.GetTextExtent(text)
        # dc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
        # dc.DrawRectangle(wx.Rect(x + (rect.width - w) // 2, rect.y + (rect.height - h) // 2, w, h))
        # dc.SetTextForeground(wx.Colour(0, 0, 0))
        # dc.DrawText(text, x + (rect.width - w) // 2, rect.y + (rect.height - h) // 2)
        # dc.DrawText(text, x + (rect.width - dc.GetTextExtent(text)[0]) // 2, rect.y + (rect.height - dc.GetTextExtent(text)[1]) // 2)

        # dc.DrawText(text, x + (rect.width - dc.GetTextExtent(text)[0]) // 2, rect.y + (rect.height - dc.GetTextExtent(text)[1]) // 2)
        super().RenderText(str(text), 0, rect, dc, state)

        return True

    def StartEditing(self, item, labelRect):
        logger.debug("StartEditing")
        return super().StartEditing(item, labelRect)

    def Activate(self, cell, model, item, col):
        logger.debug("Activate")
        return super().Activate(cell, model, item, col)

    def update_column_width(self):
        if view := self.GetView():
            dc = wx.ClientDC(view)
            w, h = dc.GetTextExtent(str(self._value))
            col = view.GetCurrentColumn()

            new_width = max(col.GetWidth(), w + 20)
            view.Columns[col].SetWidth(new_width)

        return True


class BaseTextRenderer(BaseDataViewCustomRenderer):
    def __init__(self, varianttype="string", mode=wx.dataview.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT, validators: Optional[List[Validator]] = None):
        super().__init__(varianttype=varianttype, mode=mode, align=align)

        self.validators = validators if validators else []

    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(self, parent, rect, value):
        text_ctrl = wx.TextCtrl(parent, value=str(value or ""), style=wx.TE_PROCESS_ENTER)
        text_ctrl.SetSize(rect.GetSize())
        text_ctrl.Bind(wx.EVT_CHAR, self.OnChar)
        return text_ctrl

    def GetValueFromEditorCtrl(self, editor):
        return self.GetEditorCtrl().GetValue()

    def OnChar(self, event):
        for validator in self.validators:
            if not validator.validator(event):
                wx.Bell()
                return

        event.Skip()


class BaseDataViewCtrl(wx.dataview.DataViewCtrl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

    def finish_editing(self, current_column):
        if current_column := self.CurrentColumn:
            current_column.GetRenderer().FinishEditing()

    def _on_char_hook(self, event: wx.KeyEvent):
        key_code = event.GetKeyCode()

        item = self.GetSelection()

        if not item.IsOk():
            event.Skip()
            return

        logger.debug(f"BaseDataViewCtrl._on_char_hook key_code={key_code}")
        if key_code not in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_TAB, wx.WXK_ESCAPE):
            event.Skip()
            return

        current_column = self.CurrentColumn

        current_column_render = current_column.GetRenderer()
        current_column_mode = current_column_render.GetMode()
        current_model_column = current_column.GetModelColumn()

        self.finish_editing(current_column)

        navigable_columns = [
            c.ModelColumn
            for c in self.GetColumns()
            if c.HasFlag(wx.dataview.DATAVIEW_CELL_EDITABLE | wx.dataview.DATAVIEW_CELL_ACTIVATABLE)
        ]

        if key_code == wx.WXK_TAB:
            shift_down = event.ShiftDown()

            next_column_model = current_model_column + (-1 if shift_down else 1)

            next_column = self.GetColumn(next_column_model)

            if min(navigable_columns) < next_column_model > max(navigable_columns):
                wx.Bell()
            else:
                self._current_column = next_column_model

                self.edit_item(item, next_column)

        event.Skip()

    def edit_item(self, item, column):
        """Smart edit/activate method that handles both editable and activatable cells."""
        renderer = column.GetRenderer()
        mode = renderer.GetMode()

        if mode == wx.dataview.DATAVIEW_CELL_ACTIVATABLE:
            # For activatable cells, activate programmatically
            rect = self.GetItemRect(item, column)
            rect.y -= int(self.CharHeight + (self.CharHeight / 3))
            try:
                renderer.StartEditing(item, rect)
                renderer.ActivateCell(rect, self.GetModel(), item, column.GetModelColumn(), None)
            except Exception as ex:
                logger.error(f"Error activating cell: {ex}", exc_info=True)
        else:
            # For editable cells, use EditItem
            wx.CallAfter(self.EditItem, item, column)

    def calculate_column_width(self, text, col=None):
        w = 0
        cw = 0

        if view := self.GetParent():
            dc = wx.ClientDC(view)
            w, h = dc.GetTextExtent(str(text))
            if col:
                cw = self.GetCurrentColumn().GetWidth()

        return max(cw, w + 20)


class BasePopup(wx.PopupTransientWindow):
    popup_size: wx.Size
    column_width: int = 100
    default_value: Optional[str] = None

    # on_open: Callable[..., bool] = None
    on_dismiss: Callable[..., bool]

    def __init__(self, parent):
        super().__init__(parent, flags=wx.BORDER_NONE)
        self._value = None
        self._initial = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetWindowStyle(wx.TRANSPARENT_WINDOW)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetSizer(self.sizer)

        # self.Bind(wx.EVT_CLOSE, self.close)

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
        if hasattr(self, 'on_dismiss') and self.on_dismiss:
            self.on_dismiss()

        super().Dismiss()
