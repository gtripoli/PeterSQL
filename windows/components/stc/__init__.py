from windows.components.stc.auto_complete import CompletionResult
from windows.components.stc.auto_complete import SQLAutoCompleteController, SQLCompletionProvider
from windows.components.stc.detectors import detect_syntax_id
from windows.components.stc.profiles import BASE64, CSV, HTML, JSON, MARKDOWN, REGEX, SQL, TEXT, XML, YAML
from windows.components.stc.profiles import Detector, Formatter, SyntaxProfile
from windows.components.stc.registry import SyntaxRegistry
from windows.components.stc.styles import apply_stc_theme
from windows.components.stc.themes import ThemeManager

__all__ = [
    "BASE64",
    "CSV",
    "CompletionResult",
    "Detector",
    "Formatter",
    "HTML",
    "JSON",
    "MARKDOWN",
    "REGEX",
    "SQL",
    "SQLAutoCompleteController",
    "SQLCompletionProvider",
    "SyntaxProfile",
    "SyntaxRegistry",
    "TEXT",
    "ThemeManager",
    "XML",
    "YAML",
    "apply_stc_theme",
    "detect_syntax_id",
]
