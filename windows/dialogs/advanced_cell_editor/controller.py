import wx

from windows.components.stc.detectors import detect_syntax_id
from windows.components.stc.profiles import SyntaxProfile
from windows.components.stc.styles import apply_stc_theme
from windows.views import AdvancedCellEditorDialog


class AdvancedCellEditorController(AdvancedCellEditorDialog):
    app = wx.GetApp()

    def __init__(self, parent, value: str):
        super().__init__(parent)

        self.syntax_choice.AppendItems(self.app.syntax_registry.labels())
        self.advanced_stc_editor.SetText(value or "")
        self.advanced_stc_editor.EmptyUndoBuffer()

        self.app.theme_manager.register(self.advanced_stc_editor, self._get_current_syntax_profile)

        self.syntax_choice.SetStringSelection(self._auto_syntax_profile().label)

        self.do_apply_syntax(do_format=True)

    def _auto_syntax_profile(self) -> SyntaxProfile:
        text = self.advanced_stc_editor.GetText()

        syntax_id = detect_syntax_id(text)
        return self.app.syntax_registry.get(syntax_id)

    def _get_current_syntax_profile(self) -> SyntaxProfile:
        label = self.syntax_choice.GetStringSelection()
        return self.app.syntax_registry.get(label)

    def on_syntax_changed(self, _evt):
        label = self.syntax_choice.GetStringSelection()
        self.do_apply_syntax(label)

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
