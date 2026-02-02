from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

import wx.stc

from windows.components.stc.styles import apply_stc_theme

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

    def select(self, *, syntax_id: Optional[str] = None, label: Optional[str] = None) -> SyntaxProfile:
        if syntax_id is not None:
            return self._by_id[syntax_id]
        if label is not None:
            return self._by_label[label]
        raise ValueError("Either syntax_id or label must be provided")


def apply_profile(ctrl: wx.stc.StyledTextCtrl, profile: SyntaxProfile) -> None:
    apply_stc_theme(ctrl, profile)
