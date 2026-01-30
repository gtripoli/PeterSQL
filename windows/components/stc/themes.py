from dataclasses import dataclass
import weakref
import wx


@dataclass
class _Entry:
    ref: "weakref.ReferenceType"
    get_syntax_id: callable  # () -> str


class ThemeManager:
    def __init__(self, apply_fn):
        self._apply_fn = apply_fn  # (stc_ctrl, syntax_id) -> None
        self._entries: list[_Entry] = []

    def register(self, stc_ctrl, get_syntax_id):
        self._entries.append(_Entry(weakref.ref(stc_ctrl), get_syntax_id))

    def refresh(self):
        alive: list[_Entry] = []
        for e in self._entries:
            ctrl = e.ref()
            if ctrl is None:
                continue
            try:
                self._apply_fn(ctrl, e.get_syntax_id())
                ctrl.Refresh()
            except Exception:
                pass
            alive.append(e)
        self._entries = alive
