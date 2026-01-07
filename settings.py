import copy
from typing import Any

import yaml

from helpers.observables import ObservableObject


def load(settings_file):
    settings = ObservableObject(yaml.full_load(open(settings_file)))
    settings.subscribe(lambda settings: save(settings, settings_file))
    return settings


def save(settings: dict[str, Any], settings_file) -> None:
    settings = copy.copy(settings)

    with open(settings_file, "w") as outfile:
        yaml.dump(settings, outfile, sort_keys=False)
