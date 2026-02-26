from typing import Callable, Optional

import wx
import wx.stc

from structures.engines.database import SQLDatabase, SQLTable
from windows.components.stc.sql_templates import SQL_TEMPLATES, SQLTemplate


class SQLTemplateMenuController:
    def __init__(
        self,
        editor: wx.stc.StyledTextCtrl,
        get_database: Callable[[], Optional[SQLDatabase]],
        get_current_table: Callable[[], Optional[SQLTable]]
    ):
        self._editor = editor
        self._get_database = get_database
        self._get_current_table = get_current_table
        
        self._editor.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
    
    def _on_context_menu(self, event: wx.ContextMenuEvent):
        menu = wx.Menu()
        
        template_menu = wx.Menu()
        
        for template in SQL_TEMPLATES:
            item = template_menu.Append(wx.ID_ANY, template.name, template.description)
            self._editor.Bind(
                wx.EVT_MENU,
                lambda evt, t=template: self._insert_template(t),
                item
            )
        
        menu.AppendSubMenu(template_menu, "Insert Template")
        menu.AppendSeparator()
        
        menu.Append(wx.ID_UNDO, "Undo\tCtrl+Z")
        menu.Append(wx.ID_REDO, "Redo\tCtrl+Y")
        menu.AppendSeparator()
        menu.Append(wx.ID_CUT, "Cut\tCtrl+X")
        menu.Append(wx.ID_COPY, "Copy\tCtrl+C")
        menu.Append(wx.ID_PASTE, "Paste\tCtrl+V")
        menu.AppendSeparator()
        menu.Append(wx.ID_SELECTALL, "Select All\tCtrl+A")
        
        self._editor.Bind(wx.EVT_MENU, lambda e: self._editor.Undo(), id=wx.ID_UNDO)
        self._editor.Bind(wx.EVT_MENU, lambda e: self._editor.Redo(), id=wx.ID_REDO)
        self._editor.Bind(wx.EVT_MENU, lambda e: self._editor.Cut(), id=wx.ID_CUT)
        self._editor.Bind(wx.EVT_MENU, lambda e: self._editor.Copy(), id=wx.ID_COPY)
        self._editor.Bind(wx.EVT_MENU, lambda e: self._editor.Paste(), id=wx.ID_PASTE)
        self._editor.Bind(wx.EVT_MENU, lambda e: self._editor.SelectAll(), id=wx.ID_SELECTALL)
        
        self._editor.PopupMenu(menu)
        menu.Destroy()
    
    def _insert_template(self, template: SQLTemplate):
        database = self._get_database()
        table = self._get_current_table()
        
        text = template.render(database=database, table=table)
        
        pos = self._editor.GetCurrentPos()
        self._editor.InsertText(pos, text)
        
        self._editor.SetSelection(pos, pos + len(text))
        self._editor.SetCurrentPos(pos + len(text))
