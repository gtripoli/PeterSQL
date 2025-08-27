import enum
import json
import datetime
import dataclasses


class JSONEncoder(json.encoder.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        if issubclass(o.__class__, enum.Enum):
            if isinstance(o.value, (str, int, float)):
                value = o.value
            else:
                value = json.loads(json.dumps(o.value, cls=JSONEncoder))
            return dict(name=o.name, value=value)

        if issubclass(o.__class__, enum.EnumMeta):
            return json.loads(json.dumps(dict(o.__members__.items()), cls=JSONEncoder))

        if isinstance(o, datetime.datetime):
            return o.isoformat()

        if hasattr(o, "serialize"):
            return getattr(o, "serialize")

        try:
            results = super().default(o)
        except:
            return {}

        return results
