from pathlib import Path

import wx
import wx.dataview

from constants import Language, LogLevel

from windows.dialogs.settings.repository import Settings
from windows.views import SettingsDialog


class SettingsController:
    def __init__(self, parent: wx.Window, settings: Settings) -> None:
        self.settings = settings
        self.dialog = SettingsDialog(parent)
        
        self._load_settings()
        self._populate_controls()
        self._bind_events()
    
    def _bind_events(self) -> None:
        self.dialog.apply.Bind(wx.EVT_BUTTON, self._on_apply)
        self.dialog.cancel.Bind(wx.EVT_BUTTON, self._on_cancel)
        self.dialog.shortcuts_filter.Bind(wx.EVT_SEARCH, self._on_filter_shortcuts)
    
    def _populate_controls(self) -> None:
        self._populate_languages()
        self._populate_themes()
        self._populate_advanced_settings()
        self._populate_shortcuts()
    
    def _populate_languages(self) -> None:
        self.dialog.language.Clear()
        for lang in Language:
            self.dialog.language.Append(lang.label)
    
    def _populate_shortcuts(self) -> None:
        self.dialog.shortcuts_list.DeleteAllItems()
        
        shortcuts = self.settings.get_value("shortcuts") or {}
        for action, shortcut_data in shortcuts.items():
            if isinstance(shortcut_data, dict):
                shortcut = shortcut_data.get("key", "")
                context = shortcut_data.get("context", "Global")
            else:
                shortcut = str(shortcut_data)
                context = "Global"
            
            self.dialog.shortcuts_list.AppendItem([action, shortcut, context])
    
    def _populate_themes(self) -> None:
        themes_dir = Path(wx.GetApp().GetAppName()).parent / "themes"
        if not themes_dir.exists():
            themes_dir = Path.cwd() / "themes"
        
        self.dialog.theme.Clear()
        
        if themes_dir.exists():
            for theme_file in sorted(themes_dir.glob("*.yml")):
                theme_name = theme_file.stem
                self.dialog.theme.Append(theme_name)
        
        if self.dialog.theme.GetCount() > 0:
            self.dialog.theme.SetSelection(0)
    
    def _load_settings(self) -> None:
        self._load_general_settings()
        self._load_appearance_settings()
        self._load_query_editor_settings()
        self._load_advanced_settings()
    
    def _load_advanced_settings(self) -> None:
        self.dialog.advanced_connection_timeout.SetValue(
            self.settings.get_value("advanced", "connection_timeout") or 60
        )
        self.dialog.advanced_query_timeout.SetValue(
            self.settings.get_value("advanced", "query_timeout") or 60
        )
        
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]
        logging_level = self.settings.get_value("advanced", "logging_level") or "INFO"
        try:
            selection = next(i for i, level in enumerate(levels) if level.value == logging_level)
        except StopIteration:
            selection = 1
        self.dialog.advanced_logging_level.SetSelection(selection)
    
    def _load_appearance_settings(self) -> None:
        current_theme = self.settings.get_value("appearance", "theme") or ""
        if current_theme:
            idx = self.dialog.theme.FindString(current_theme)
            if idx != wx.NOT_FOUND:
                self.dialog.theme.SetSelection(idx)
        
        appearance_mode = self.settings.get_value("appearance", "mode") or "auto"
        if appearance_mode == "auto":
            self.dialog.appearance_mode_auto.SetValue(True)
        elif appearance_mode == "light":
            self.dialog.appearance_mode_light.SetValue(True)
        elif appearance_mode == "dark":
            self.dialog.appearance_mode_dark.SetValue(True)
    
    def _load_general_settings(self) -> None:
        language_map = {lang.code: idx for idx, lang in enumerate(Language)}
        language = self.settings.get_value("language") or "en_US"
        self.dialog.language.SetSelection(language_map.get(language, 0))
    
    def _load_query_editor_settings(self) -> None:
        self.dialog.query_editor_statement_separator.SetValue(
            self.settings.get_value("query_editor", "statement_separator") or ";"
        )
        self.dialog.query_editor_trim_whitespace.SetValue(
            self.settings.get_value("query_editor", "trim_whitespace") or False
        )
        self.dialog.query_editor_execute_selected_only.SetValue(
            self.settings.get_value("query_editor", "execute_selected_only") or False
        )
        
        autocomplete = self.settings.get_value("query_editor", "autocomplete")
        self.dialog.query_editor_autocomplete.SetValue(
            autocomplete if autocomplete is not None else True
        )
        
        autoformat = self.settings.get_value("query_editor", "autoformat")
        self.dialog.query_editor_format.SetValue(
            autoformat if autoformat is not None else True
        )
    
    def _save_settings(self) -> None:
        self._save_general_settings()
        self._save_appearance_settings()
        self._save_query_editor_settings()
        self._save_advanced_settings()
    
    def _save_advanced_settings(self) -> None:
        if not self.settings.get_value("advanced"):
            self.settings.set_value("advanced", value={})
        
        self.settings.set_value("advanced", "connection_timeout", 
            value=self.dialog.advanced_connection_timeout.GetValue()
        )
        self.settings.set_value("advanced", "query_timeout", 
            value=self.dialog.advanced_query_timeout.GetValue()
        )
        
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]
        selection = self.dialog.advanced_logging_level.GetSelection()
        self.settings.set_value("advanced", "logging_level", 
            value=levels[selection].value if 0 <= selection < len(levels) else LogLevel.INFO.value
        )
    
    def _save_appearance_settings(self) -> None:
        if not self.settings.get_value("appearance"):
            self.settings.set_value("appearance", value={})
        
        theme_idx = self.dialog.theme.GetSelection()
        if theme_idx != wx.NOT_FOUND:
            self.settings.set_value("appearance", "theme", value=self.dialog.theme.GetString(theme_idx))
        
        if self.dialog.appearance_mode_auto.GetValue():
            appearance_mode = "auto"
        elif self.dialog.appearance_mode_light.GetValue():
            appearance_mode = "light"
        else:
            appearance_mode = "dark"
        self.settings.set_value("appearance", "mode", value=appearance_mode)
    
    def _save_general_settings(self) -> None:
        language_map = {idx: lang.code for idx, lang in enumerate(Language)}
        self.settings.set_value("language", value=language_map.get(
            self.dialog.language.GetSelection(), "en_US"
        ))
    
    def _save_query_editor_settings(self) -> None:
        if not self.settings.get_value("query_editor"):
            self.settings.set_value("query_editor", value={})
        
        self.settings.set_value("query_editor", "statement_separator", 
            value=self.dialog.query_editor_statement_separator.GetValue()
        )
        self.settings.set_value("query_editor", "trim_whitespace", 
            value=self.dialog.query_editor_trim_whitespace.GetValue()
        )
        self.settings.set_value("query_editor", "execute_selected_only", 
            value=self.dialog.query_editor_execute_selected_only.GetValue()
        )
        self.settings.set_value("query_editor", "autocomplete", 
            value=self.dialog.query_editor_autocomplete.GetValue()
        )
        self.settings.set_value("query_editor", "autoformat", 
            value=self.dialog.query_editor_format.GetValue()
        )
    
    def _on_apply(self, event: wx.Event) -> None:
        self._save_settings()
        self.dialog.EndModal(wx.ID_OK)
    
    def _on_cancel(self, event: wx.Event) -> None:
        self.dialog.EndModal(wx.ID_CANCEL)
    
    def _on_filter_shortcuts(self, event: wx.Event) -> None:
        filter_text = self.dialog.shortcuts_filter.GetValue().lower()
        
        self.dialog.shortcuts_list.DeleteAllItems()
        
        shortcuts = self.settings.get_value("shortcuts") or {}
        
        for action, shortcut_data in shortcuts.items():
            if isinstance(shortcut_data, dict):
                shortcut = shortcut_data.get("key", "")
                context = shortcut_data.get("context", "Global")
            else:
                shortcut = str(shortcut_data)
                context = "Global"
            
            if (not filter_text or 
                filter_text in action.lower() or 
                filter_text in shortcut.lower() or 
                filter_text in context.lower()):
                self.dialog.shortcuts_list.AppendItem([action, shortcut, context])
    
    def show_modal(self) -> int:
        return self.dialog.ShowModal()
