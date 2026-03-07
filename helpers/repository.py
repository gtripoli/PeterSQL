from pathlib import Path
from typing import Any, Generic, TypeVar

import yaml


T = TypeVar('T')


class YamlRepository(Generic[T]):
    def __init__(self, config_file: Path):
        self._config_file = config_file
    
    def _read_yaml(self) -> dict[str, Any]:
        try:
            with open(self._config_file, 'r') as file:
                data = yaml.full_load(file)
                return data or {}
        except Exception:
            return {}
    
    def _write_yaml(self, data: Any) -> None:
        with open(self._config_file, 'w') as file:
            yaml.dump(data, file, sort_keys=False)
