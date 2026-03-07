import wx
import wx.dataview

from windows.components.stc.autocomplete.completion_types import CompletionItem, CompletionItemType
from windows.components.stc.theme_loader import ThemeLoader


class AutoCompletePopup(wx.PopupWindow):
    def __init__(self, parent: wx.Window, settings: object = None, theme_loader: ThemeLoader = None) -> None:
        super().__init__(parent, wx.BORDER_SIMPLE)
        
        self._selected_index: int = 0
        self._items: list[CompletionItem] = []
        self._on_item_selected: callable = None
        self._settings = settings
        self._theme_loader = theme_loader
        
        if settings:
            self._popup_width = settings.get_value("settings", "autocomplete", "popup_width") or 300
            self._popup_max_height = settings.get_value("settings", "autocomplete", "popup_max_height") or 10
        else:
            self._popup_width = 300
            self._popup_max_height = 10
        
        self._create_ui()
        self._bind_events()
    
    def _create_ui(self) -> None:
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._list_ctrl = wx.ListCtrl(
            panel,
            style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL
        )
        
        self._image_list = wx.ImageList(16, 16)
        self._list_ctrl.SetImageList(self._image_list, wx.IMAGE_LIST_SMALL)
        
        self._list_ctrl.InsertColumn(0, "", width=self._popup_width)
        self._list_ctrl.SetMinSize((self._popup_width, 200))
        
        sizer.Add(self._list_ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
    
    def _bind_events(self) -> None:
        self._list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_activated)
        self._list_ctrl.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)
    
    def show_items(self, items: list[CompletionItem], position: wx.Point) -> None:
        self._items = items
        self._selected_index = 0
        
        self._list_ctrl.DeleteAllItems()
        self._image_list.RemoveAll()
        
        for idx, item in enumerate(items):
            bitmap = self._get_bitmap_for_type(item.item_type)
            color = self._get_color_for_type(item.item_type)
            
            image_idx = self._image_list.Add(bitmap)
            list_idx = self._list_ctrl.InsertItem(idx, item.name, image_idx)
            
            if color:
                self._list_ctrl.SetItemTextColour(list_idx, color)
        
        if items:
            self._list_ctrl.Select(0)
            self._list_ctrl.Focus(0)
        
        self.SetPosition(position)
        
        item_count = min(len(items), self._popup_max_height)
        item_height = 24
        height = item_count * item_height + 10
        self.SetSize((self._popup_width, height))
        
        self.Show()
        self._list_ctrl.SetFocus()
    
    def _get_bitmap_for_type(self, item_type: CompletionItemType) -> wx.Bitmap:
        icon_map = {
            CompletionItemType.KEYWORD: wx.ART_INFORMATION,
            CompletionItemType.FUNCTION: wx.ART_EXECUTABLE_FILE,
            CompletionItemType.TABLE: wx.ART_FOLDER,
            CompletionItemType.COLUMN: wx.ART_NORMAL_FILE,
        }
        
        art_id = icon_map.get(item_type, wx.ART_INFORMATION)
        return wx.ArtProvider.GetBitmap(art_id, wx.ART_MENU, (16, 16))
    
    def _get_color_for_type(self, item_type: CompletionItemType) -> wx.Colour:
        if self._theme_loader:
            colors = self._theme_loader.get_autocomplete_colors()
            color_hex = colors.get(item_type.value)
            if color_hex:
                return wx.Colour(color_hex)
        
        color_map = {
            CompletionItemType.KEYWORD: wx.Colour(0, 0, 255),
            CompletionItemType.FUNCTION: wx.Colour(128, 0, 128),
            CompletionItemType.TABLE: wx.Colour(0, 128, 0),
            CompletionItemType.COLUMN: wx.Colour(0, 0, 0),
        }
        return color_map.get(item_type, wx.Colour(0, 0, 0))
    
    def _on_item_activated(self, event: wx.Event) -> None:
        row = self._list_ctrl.GetFirstSelected()
        if row != wx.NOT_FOUND and row < len(self._items):
            self._complete_with_item(self._items[row])
    
    def _on_key_down(self, event: wx.KeyEvent) -> None:
        key_code = event.GetKeyCode()
        
        if key_code == wx.WXK_ESCAPE:
            self.Hide()
            return
        
        if key_code in (wx.WXK_RETURN, wx.WXK_TAB):
            row = self._list_ctrl.GetFirstSelected()
            if row != wx.NOT_FOUND and row < len(self._items):
                self._complete_with_item(self._items[row])
            return
        
        if key_code == wx.WXK_PAGEDOWN:
            current = self._list_ctrl.GetFirstSelected()
            if current != wx.NOT_FOUND:
                new_index = min(current + self._popup_max_height, len(self._items) - 1)
                self._list_ctrl.Select(new_index)
                self._list_ctrl.Focus(new_index)
                self._list_ctrl.EnsureVisible(new_index)
            return
        
        if key_code == wx.WXK_PAGEUP:
            current = self._list_ctrl.GetFirstSelected()
            if current != wx.NOT_FOUND:
                new_index = max(current - self._popup_max_height, 0)
                self._list_ctrl.Select(new_index)
                self._list_ctrl.Focus(new_index)
                self._list_ctrl.EnsureVisible(new_index)
            return
        
        event.Skip()
    
    def _on_kill_focus(self, event: wx.FocusEvent) -> None:
        self.Hide()
        event.Skip()
    
    def _complete_with_item(self, item: CompletionItem) -> None:
        if self._on_item_selected:
            self._on_item_selected(item)
        self.Hide()
    
    def set_on_item_selected(self, callback: callable) -> None:
        self._on_item_selected = callback
    
    def get_selected_item(self) -> CompletionItem:
        row = self._list_ctrl.GetFirstSelected()
        if row != wx.NOT_FOUND and row < len(self._items):
            return self._items[row]
        return None
