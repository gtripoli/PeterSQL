import wx.stc

from windows.components.stc.styles import apply_stc_theme

from windows.components.stc.profiles import Detector, Formatter, SyntaxProfile
from windows.components.stc.registry import SyntaxRegistry

__all__ = [
    "Detector",
    "Formatter",
    "SyntaxProfile",
    "SyntaxRegistry",
    "apply_profile",
]


def apply_profile(ctrl: wx.stc.StyledTextCtrl, profile: SyntaxProfile) -> None:
    apply_stc_theme(ctrl, profile)
