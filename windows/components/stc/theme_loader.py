from pathlib import Path
from typing import Optional

import wx
import yaml


class ThemeLoader:
    def __init__(self, themes_dir: Path) -> None:
        self._themes_dir = themes_dir
        self._current_theme: Optional[dict] = None
        self._theme_name: Optional[str] = None
    
    def load_theme(self, theme_name: str) -> None:
        theme_file = self._themes_dir / f"{theme_name}.yml"
        if not theme_file.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_file}")
        
        with open(theme_file, 'r') as f:
            self._current_theme = yaml.safe_load(f)
            self._theme_name = theme_name
    
    def get_palette(self) -> dict[str, str]:
        if not self._current_theme:
            return self._get_default_palette()
        
        is_dark = wx.SystemSettings.GetAppearance().IsDark()
        mode = "dark" if is_dark else "light"
        
        editor_colors = self._current_theme.get("editor", {}).get(mode, {})
        
        palette = {}
        for key, value in editor_colors.items():
            if value == "auto":
                palette[key] = self._get_system_color(key)
            else:
                palette[key] = value
        
        return palette
    
    def get_autocomplete_colors(self) -> dict[str, str]:
        if not self._current_theme:
            return self._get_default_autocomplete_colors()
        
        is_dark = wx.SystemSettings.GetAppearance().IsDark()
        mode = "dark" if is_dark else "light"
        
        return self._current_theme.get("autocomplete", {}).get(mode, {})
    
    def _get_system_color(self, key: str) -> str:
        color_map = {
            "background": wx.SYS_COLOUR_WINDOW,
            "foreground": wx.SYS_COLOUR_WINDOWTEXT,
            "line_number_background": wx.SYS_COLOUR_3DFACE,
            "line_number_foreground": wx.SYS_COLOUR_GRAYTEXT,
        }
        
        if key in color_map:
            color = wx.SystemSettings.GetColour(color_map[key])
            return f"#{color.Red():02x}{color.Green():02x}{color.Blue():02x}"
        
        return "#000000"
    
    def _get_default_palette(self) -> dict[str, str]:
        is_dark = wx.SystemSettings.GetAppearance().IsDark()
        
        if is_dark:
            return {
                "background": self._get_system_color("background"),
                "foreground": self._get_system_color("foreground"),
                "line_number_background": self._get_system_color("line_number_background"),
                "line_number_foreground": self._get_system_color("line_number_foreground"),
                "keyword": "#569cd6",
                "string": "#ce9178",
                "comment": "#6a9955",
                "number": "#b5cea8",
                "operator": self._get_system_color("foreground"),
                "property": "#9cdcfe",
                "error": "#f44747",
                "uri": "#4ec9b0",
                "reference": "#4ec9b0",
                "document": "#c586c0",
            }
        
        return {
            "background": self._get_system_color("background"),
            "foreground": self._get_system_color("foreground"),
            "line_number_background": self._get_system_color("line_number_background"),
            "line_number_foreground": self._get_system_color("line_number_foreground"),
            "keyword": "#0000ff",
            "string": "#990099",
            "comment": "#007f00",
            "number": "#ff6600",
            "operator": "#000000",
            "property": "#0033aa",
            "error": "#cc0000",
            "uri": "#006666",
            "reference": "#006666",
            "document": "#7a1fa2",
        }
    
    def _get_default_autocomplete_colors(self) -> dict[str, str]:
        is_dark = wx.SystemSettings.GetAppearance().IsDark()
        
        if is_dark:
            return {
                "keyword": "#569cd6",
                "function": "#dcdcaa",
                "table": "#4ec9b0",
                "column": "#9cdcfe",
            }
        
        return {
            "keyword": "#0000ff",
            "function": "#800080",
            "table": "#008000",
            "column": "#000000",
        }
