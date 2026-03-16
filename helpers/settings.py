from pathlib import Path
from typing import Any, Optional

from helpers.repository import YamlRepository
from helpers.observables import ObservableObject


class Settings(ObservableObject):
    _default_unset = object()

    def _ensure_root(self) -> dict[str, Any]:
        value = super()._get_value()
        if isinstance(value, dict):
            return value

        value = {}
        super()._set_value(value)

        return value

    def _persist_default(self, attributes: tuple[str, ...], default: Any) -> Any:
        if not attributes:
            return super()._get_value()

        root = self._ensure_root()
        current = root

        for attribute in attributes[:-1]:
            nested = current.get(attribute)
            if not isinstance(nested, dict):
                nested = {}
                current[attribute] = nested
            current = nested

        last_attribute = attributes[-1]
        if current.get(last_attribute) is None:
            current[last_attribute] = default
            super()._set_value(root)

        return current.get(last_attribute)

    def get_value(self, *attributes: str, default: Any = _default_unset) -> Any:
        value = super().get_value(*attributes)
        if value is not None:
            return value

        if default is self._default_unset:
            return None

        return self._persist_default(attributes, default)


class SettingsRepository(YamlRepository[Settings]):
    def __init__(self, config_file: Path):
        super().__init__(config_file)
        self.settings: Optional[Settings] = None

    def _write(self) -> None:
        if self.settings is None:
            return

        data = dict(self.settings.get_value(default={}))
        self._write_yaml(data)

    def load(self) -> Settings:
        data = self._read_yaml()
        self.settings = Settings(data)
        self.settings.subscribe(lambda _: self._write())
        return self.settings