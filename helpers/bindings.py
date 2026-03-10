import abc
import enum

from typing import Optional, Union, Any, TypeAlias, Callable

import wx
import wx.stc

from helpers.observables import Observable, CallbackEvent

CONTROL_BIND_LABEL: TypeAlias = wx.StaticText
CONTROL_BIND_VALUE: TypeAlias = Union[wx.TextCtrl, wx.SpinCtrl, wx.CheckBox]
CONTROL_BIND_PATH: TypeAlias = Union[wx.FilePickerCtrl, wx.DirPickerCtrl]
CONTROL_BIND_SELECTION: TypeAlias = wx.Choice
CONTROL_BIND_COMBO: TypeAlias = wx.ComboBox
CONTROL_BIND_STC: TypeAlias = wx.stc.StyledTextCtrl
CONTROL_BIND_RADIO_GROUP: TypeAlias = list[wx.RadioButton]
CONTROLS: TypeAlias = Union[CONTROL_BIND_LABEL, CONTROL_BIND_VALUE, CONTROL_BIND_PATH, CONTROL_BIND_SELECTION, CONTROL_BIND_COMBO, CONTROL_BIND_STC, CONTROL_BIND_RADIO_GROUP]


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
    def __init__(self, control: CONTROL_BIND_SELECTION, observable: Observable, initial: Optional[list[str]] = None):
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


class BindComboControl(AbstractBindControl):
    def __init__(self, control: CONTROL_BIND_COMBO, observable: Observable):
        super().__init__(control, observable, event=wx.EVT_TEXT)

    def clear(self) -> None:
        self.control.SetValue(self.initial if self.initial is not None else "")

    def get(self) -> str:
        return self.control.GetValue()

    def set(self, value: Any) -> None:
        self.control.SetValue(str(value))


class BindStyledTextControl(AbstractBindControl):
    def __init__(self, control: CONTROL_BIND_STC, observable: Observable):
        super().__init__(control, observable, event=wx.stc.EVT_STC_CHANGE)

    def clear(self) -> None:
        self.control.SetText(self.initial if self.initial is not None else "")

    def get(self) -> str:
        return self.control.GetText()

    def set(self, value: Any) -> None:
        self.control.SetText(str(value))


class BindRadioGroupControl(AbstractBindControl):
    def __init__(self, radios: CONTROL_BIND_RADIO_GROUP, observable: Observable):
        self.radios = radios
        self.control = radios[0] if radios else None
        self.initial = self.get()
        self.observable = observable

        self.observable.subscribe(self._set_value, CallbackEvent.AFTER_CHANGE)

        for radio in self.radios:
            radio.Bind(wx.EVT_RADIOBUTTON, self.handle_control_event)

        if (value := self.observable.get_value()) is not None:
            self.set(value)

    def clear(self) -> None:
        if self.radios:
            self.radios[0].SetValue(True)

    def get(self) -> Optional[str]:
        for radio in self.radios:
            if radio.GetValue():
                return radio.GetLabel()
        return None

    def set(self, value: Any) -> None:
        value_str = str(value).upper()
        for radio in self.radios:
            if radio.GetLabel().upper() == value_str:
                radio.SetValue(True)
                return


class AbstractMetaModel(abc.ABCMeta):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        for attr_name, value in attrs.items():
            if isinstance(value, Observable):
                value.name = attr_name


class AbstractModel(metaclass=AbstractMetaModel):
    observables: list[Observable] = []

    def bind_control(self, control: CONTROLS, observable: Observable):
        if isinstance(control, wx.StaticText):
            BindLabelControl(control, observable)
        elif isinstance(control, (wx.TextCtrl, wx.SpinCtrl, wx.CheckBox)):
            BindValueControl(control, observable)
        elif isinstance(control, (wx.FilePickerCtrl, wx.DirPickerCtrl)):
            BindPathControl(control, observable)
        elif isinstance(control, wx.Choice):
            BindSelectionControl(control, observable)
        elif isinstance(control, wx.ComboBox):
            BindComboControl(control, observable)
        elif isinstance(control, wx.stc.StyledTextCtrl):
            BindStyledTextControl(control, observable)
        elif isinstance(control, list) and control and isinstance(control[0], wx.RadioButton):
            BindRadioGroupControl(control, observable)

        self.observables.append(observable)

    def bind_controls(self, **controls: Union[CONTROLS, tuple[CONTROLS, dict]]):
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


def wx_call_after_debounce(*observables: Observable, callback: Callable, wait_time: float = 0.4):
    waiting = False

    def _debounced(*args, **kwargs):
        nonlocal waiting
        if not waiting:
            waiting = True

            def call_and_reset():
                nonlocal waiting
                callback(*args, **kwargs)
                waiting = False

            wx.CallAfter(call_and_reset)

    for obs in observables:
        setattr(obs, '_debounce_callback', _debounced)
        obs.subscribe(_debounced)
