"""Global constants for PeterSQL application."""

import os
from pathlib import Path
from enum import Enum


WORKDIR = Path(os.path.abspath(os.path.dirname(__file__)))


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Language(Enum):
    EN_US = ("en_US", "English")
    IT_IT = ("it_IT", "Italiano")
    FR_FR = ("fr_FR", "Français")
    ES_ES = ("es_ES", "Español")
    DE_DE = ("de_DE", "Deutsch")
    
    def __init__(self, code: str, label: str):
        self.code = code
        self.label = label
    
    @classmethod
    def get_codes(cls) -> list[str]:
        return [lang.code for lang in cls]
    
    @classmethod
    def get_labels(cls) -> list[str]:
        return [lang.label for lang in cls]
    
    @classmethod
    def from_code(cls, code: str) -> "Language":
        for lang in cls:
            if lang.code == code:
                return lang
        return cls.EN_US
