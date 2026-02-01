from dataclasses import dataclass
from typing import Callable, List
import weakref

import wx


@dataclass
class _Entry:
    ref: "weakref.ReferenceType"
    get_syntax_id: Callable[[], str]


class ThemeManager:
    def __init__(self, apply_fn: Callable[[wx.stc.StyledTextCtrl, str], None]):
        self._apply_fn = apply_fn
        self._entries: List[_Entry] = []

    def register(self, stc_ctrl: wx.stc.StyledTextCtrl, get_syntax_id: Callable[[], str]):
        self._entries.append(_Entry(weakref.ref(stc_ctrl), get_syntax_id))

    def refresh(self):
        alive: List[_Entry] = []
        for entry in self._entries:
            ctrl = entry.ref()
            if ctrl is None:
                continue
            try:
                self._apply_fn(ctrl, entry.get_syntax_id())
                ctrl.Refresh()
            except Exception:
                continue
            alive.append(entry)
        self._entries = alive
