import wx


class QueryMixin:
    def on_new_query(self, event):
        new_panel = wx.Panel(self.notebook_query_editor)
        sizer = wx.BoxSizer(wx.VERTICAL)
        stc = wx.stc.StyledTextCtrl(new_panel, style=0)
        sizer.Add(stc, 1, wx.EXPAND)
        new_panel.SetSizer(sizer)
        n = self.notebook_query_editor.GetPageCount() + 1
        self.notebook_query_editor.AddPage(new_panel, f"Query #{n}", select=True)

    def on_close_query(self, event):
        n = self.notebook_query_editor.GetSelection()
        if n != wx.NOT_FOUND:
            self.notebook_query_editor.DeletePage(n)