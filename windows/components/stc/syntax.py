from dataclasses import dataclass
from typing import Sequence, Optional, Callable, List, Dict

import wx.stc

Formatter = Callable[[str], str]
Detector = Callable[[str], bool]

@dataclass(frozen=True)
class SyntaxProfile:
    id: str
    label: str
    stc_lexer: int
    keywords: Sequence[str] = ()
    formatter: Optional[Formatter] = None
    detector: Optional[Detector] = None  # used for AUTO



class SyntaxRegistry:
    def __init__(self, profiles: Sequence[SyntaxProfile]):
        self._profiles: List[SyntaxProfile] = list(profiles)
        self._by_id: Dict[str, SyntaxProfile] = {p.id: p for p in self._profiles}
        self._by_label: Dict[str, SyntaxProfile] = {p.label: p for p in self._profiles}

    def labels(self) -> List[str]:
        return [p.label for p in self._profiles]

    def get(self, syntax_id: str) -> SyntaxProfile:
        return self._by_id[syntax_id]

    def by_label(self, label: str) -> SyntaxProfile:
        return self._by_label[label]

    def all(self) -> List[SyntaxProfile]:
        return list(self._profiles)


def apply_profile(ctrl: wx.stc.StyledTextCtrl, profile: SyntaxProfile) -> None:
    """Apply lexer + keywords. (Colors/theme can be centralized here later.)"""
    ctrl.SetLexer(profile.stc_lexer)

    if profile.keywords:
        ctrl.SetKeyWords(0, " ".join(profile.keywords))
    else:
        ctrl.SetKeyWords(0, "")

    # Reasonable defaults (IDE-ish)
    ctrl.SetTabWidth(4)
    ctrl.SetUseTabs(False)
    ctrl.SetWrapMode(wx.stc.STC_WRAP_NONE)

    # Line numbers margin
    ctrl.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
    ctrl.SetMarginWidth(0, 40)