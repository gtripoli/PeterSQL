from pathlib import Path
from typing import Optional

from helpers.observables import ObservableObject
from helpers.repository import YamlRepository


class SettingsRepository(YamlRepository[ObservableObject]):
    def __init__(self, config_file: Path):
        super().__init__(config_file)
        self.settings: Optional[ObservableObject] = None
    
    def _write(self) -> None:
        if self.settings is None:
            return
        
        data = dict(self.settings.get_value())
        self._write_yaml(data)
    
    def load(self) -> ObservableObject:
        data = self._read_yaml()
        self.settings = ObservableObject(data)
        self.settings.subscribe(lambda _: self._write())
        return self.settings


class Settings(SettingsRepository):
    pass
