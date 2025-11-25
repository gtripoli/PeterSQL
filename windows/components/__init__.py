import wx
import wx.dataview
from typing import Any, Self, Callable, List, Optional


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
        print("StartEditing")
        print(item, labelRect)
        return super().StartEditing(item, labelRect)

    def Activate(self, cell, model, item, col):
        print("Activate")
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
