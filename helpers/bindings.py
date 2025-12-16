import abc
import enum

from typing import Optional, Union, Any, List, TypeAlias, Dict, Tuple, Callable

import wx

from helpers.observables import Observable, CallbackEvent

CONTROL_BIND_LABEL: TypeAlias = wx.StaticText
CONTROL_BIND_VALUE: TypeAlias = Union[wx.TextCtrl, wx.SpinCtrl, wx.CheckBox]
CONTROL_BIND_PATH: TypeAlias = Union[wx.FilePickerCtrl, wx.DirPickerCtrl]
CONTROL_BIND_SELECTION: TypeAlias = wx.Choice
CONTROLS: TypeAlias = Union[CONTROL_BIND_LABEL, CONTROL_BIND_VALUE, CONTROL_BIND_PATH, CONTROL_BIND_SELECTION]


class AbstractBindControl(abc.ABC):
    control: CONTROLS
    initial: Any
    observable: Observable

    def __init__(self, control: CONTROLS, observable: Observable, event: Optional[wx.PyEventBinder] = None):
        self.control = control
        self.initial = self.get()
        self.observable = observable

        self.observable.subscribe(self._set_value, CallbackEvent.AFTER_CHANGE)

        if event is not None:
            self.control.Bind(event, self.handle_control_event)

        if (value := self.observable.get_value()) is not None:
            self.set(value)

    def handle_control_event(self, event: Union[wx.Event, wx.CommandEvent]):
        value = self.get()
        if value != self.observable.get_value():
            self.observable.set_value(value)

    def _set_value(self, value: Any):
        if value != self.get():
            if value is not None and str(value).strip() != "":
                self.set(value)
            else:
                self.clear()

    @abc.abstractmethod
    def clear(self) -> None:
        ...

    @abc.abstractmethod
    def set(self, value: Any):
        ...

    @abc.abstractmethod
    def get(self) -> Any:
        ...


class BindLabelControl(AbstractBindControl):
    def clear(self):
        self.control.SetLabel(self.initial)

    def get(self) -> str:
        return self.control.GetLabel()

    def set(self, value: Any):
        self.control.SetLabel(str(value))


class BindValueControl(AbstractBindControl):
    def __init__(self, control: CONTROL_BIND_VALUE, observable: Observable):
        event = None
        if isinstance(control, wx.TextCtrl):
            event = wx.EVT_TEXT
        elif isinstance(control, wx.SpinCtrl):
            event = wx.EVT_SPINCTRL
        elif isinstance(control, wx.CheckBox):
            event = wx.EVT_CHECKBOX
        super().__init__(control, observable, event=event)

    def clear(self) -> None:
        if isinstance(self.control, wx.CheckBox):
            self.control.SetValue(False)
        elif isinstance(self.control, wx.SpinCtrl):
            self.control.SetValue(0)
        else:
            self.control.SetValue(self.initial if self.initial is not None else "")

    def set(self, value: Any) -> None:
        if isinstance(self.control, wx.CheckBox):
            self.control.SetValue(bool(value))
        elif isinstance(self.control, wx.SpinCtrl):
            self.control.SetValue(int(value))
        else:
            self.control.SetValue(str(value))

    def get(self) -> Any:
        if isinstance(self.control, wx.CheckBox):
            return bool(self.control.GetValue())
        elif isinstance(self.control, wx.SpinCtrl):
            return int(self.control.GetValue())

        return self.control.GetValue()


class BindSelectionControl(AbstractBindControl):
    def __init__(self, control: CONTROL_BIND_SELECTION, observable: Observable, initial: Optional[List[str]] = None):
        super().__init__(control, observable, event=wx.EVT_CHOICE)
        if initial is not None:
            self.control.Set(initial)

    def clear(self) -> None:
        self.control.SetSelection(wx.NOT_FOUND)

    def get(self) -> str:
        return self.control.GetStringSelection()

    def set(self, value: Any):
        if isinstance(value, enum.Enum):
            value = value.name

        if isinstance(value, str):
            if (index := self.control.FindString(value)) != wx.NOT_FOUND:
                self.control.SetSelection(index)
            else:
                self.control.SetSelection(wx.NOT_FOUND)
        elif isinstance(value, int):
            self.control.SetSelection(value)
        else:
            self.control.SetSelection(wx.NOT_FOUND)


class BindPathControl(AbstractBindControl):
    def __init__(self, control: CONTROL_BIND_PATH, observable: Observable):
        event = None
        if isinstance(control, wx.FilePickerCtrl):
            event = wx.EVT_FILEPICKER_CHANGED
        elif isinstance(control, wx.DirPickerCtrl):
            event = wx.EVT_DIRPICKER_CHANGED

        super().__init__(control, observable, event=event)

    def clear(self) -> None:
        self.control.SetPath("")

    def get(self) -> str:
        return self.control.GetPath()

    def set(self, value: Any) -> None:
        self.control.SetPath(str(value))


class AbstractMetaModel(abc.ABCMeta):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        for attr_name, value in attrs.items():
            if isinstance(value, Observable):
                value.name = attr_name


class AbstractModel(metaclass=AbstractMetaModel):
    observables: List[Observable] = []

    def bind_control(self, control: CONTROLS, observable: Observable, **kwargs):
        if isinstance(control, wx.StaticText):
            BindLabelControl(control, observable, **kwargs)
        elif isinstance(control, (wx.TextCtrl, wx.SpinCtrl, wx.CheckBox)):
            BindValueControl(control, observable)
        elif isinstance(control, (wx.FilePickerCtrl, wx.DirPickerCtrl)):
            BindPathControl(control, observable)
        elif isinstance(control, wx.Choice):
            BindSelectionControl(control, observable, **kwargs)

        self.observables.append(observable)

    def bind_controls(self, **controls: Union[CONTROLS, Tuple[CONTROLS, Dict]]):
        for name, ctrl in controls.items():
            if hasattr(self, name) and isinstance(getattr(self, name), Observable):
                observable = getattr(self, name)
                if isinstance(ctrl, tuple):
                    self.bind_control(ctrl[0], observable, **ctrl[1])
                else:
                    self.bind_control(ctrl, observable)

    def subscribe(self, callback: Callable):
        for observable in self.observables:
            observable.subscribe(callback)
