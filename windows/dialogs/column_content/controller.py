from typing import Optional

import wx

from windows.components.stc.detectors import detect_syntax_id
from windows.components.stc.profiles import SyntaxProfile
from windows.components.stc.styles import apply_stc_theme
from windows.views import ColumnContentDialog


class ColumnContentDialogController(ColumnContentDialog):
    app = wx.GetApp()

    def __init__(self, parent, value: str, read_only: bool = False):
        super().__init__(parent)

        self._read_only = read_only

        self.syntax_choice.AppendItems(self.app.syntax_registry.labels())
        self.advanced_stc_editor.SetText(value or "")
        self.advanced_stc_editor.EmptyUndoBuffer()

        self.app.theme_manager.register(self.advanced_stc_editor, self._get_current_syntax_profile)

        self.syntax_choice.SetStringSelection(self._auto_syntax_profile().label)

        self.do_apply_syntax(do_format=True)
        self._apply_read_only_state()

        self.m_button48.Bind(wx.EVT_BUTTON, self._on_ok)
        self.m_button49.Bind(wx.EVT_BUTTON, self._on_cancel)

    def _auto_syntax_profile(self) -> SyntaxProfile:
        text = self.advanced_stc_editor.GetText()

        syntax_id = detect_syntax_id(text)
        return self.app.syntax_registry.get(syntax_id)

    def _get_current_syntax_profile(self) -> SyntaxProfile:
        label = self.syntax_choice.GetStringSelection()
        return self.app.syntax_registry.get(label)

    def on_syntax_changed(self, _evt):
        self.do_apply_syntax(do_format=True)

    def _apply_read_only_state(self) -> None:
        if not self._read_only:
            return

        self.advanced_stc_editor.SetReadOnly(True)
        self.m_button49.Hide()
        self.m_button48.SetLabel("Close")
        self.Layout()

    def _on_ok(self, _evt: wx.Event) -> None:
        self.EndModal(wx.ID_OK)

    def _on_cancel(self, _evt: wx.Event) -> None:
        self.EndModal(wx.ID_CANCEL)

    def do_apply_syntax(self, do_format: bool = True):
        label = self.syntax_choice.GetStringSelection()
        syntax_profile = self.app.syntax_registry.by_label(label)

        apply_stc_theme(self.advanced_stc_editor, syntax_profile)

        if do_format and syntax_profile.formatter:
            old = self.advanced_stc_editor.GetText()
            try:
                formatted = syntax_profile.formatter(old)
            except Exception:
                return

            if formatted != old:
                self._replace_text_undo_friendly(formatted)

    def _replace_text_undo_friendly(self, new_text: str):
        self.advanced_stc_editor.BeginUndoAction()
        try:
            self.advanced_stc_editor.SetText(new_text)
        finally:
            self.advanced_stc_editor.EndUndoAction()

    def get_value(self) -> Optional[str]:
        return self.advanced_stc_editor.GetText()