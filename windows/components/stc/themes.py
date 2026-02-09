import weakref

from dataclasses import dataclass
from typing import Callable

import wx
import wx.stc

from windows.components.stc.profiles import SyntaxProfile


@dataclass
class _Entry:
    reference: "weakref.ReferenceType[wx.stc.StyledTextCtrl]"
    get_syntax_profile: Callable[[], SyntaxProfile]


class ThemeManager:
    def __init__(
        self,
        apply_function: Callable[[wx.stc.StyledTextCtrl, SyntaxProfile], None],
    ) -> None:
        self._apply_function = apply_function
        self._entries: list[_Entry] = []

    def refresh(self) -> None:
        alive: list[_Entry] = []
        for entry in self._entries:
            ctrl = entry.reference()
            if ctrl is None:
                continue
            try:
                self._apply_function(ctrl, entry.get_syntax_profile())
                ctrl.Refresh()
            except Exception:
                continue
            alive.append(entry)
        self._entries = alive

    def register(
        self,
        stc_ctrl: wx.stc.StyledTextCtrl,
        get_syntax_profile: Callable[[], SyntaxProfile],
    ) -> None:
        self._entries.append(_Entry(weakref.ref(stc_ctrl), get_syntax_profile))
