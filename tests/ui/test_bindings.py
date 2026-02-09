import pytest

import wx

from helpers.observables import Observable
from helpers.bindings import (
    BindLabelControl,
    BindValueControl,
    BindSelectionControl,
    BindPathControl,
    AbstractModel,
)


class TestBindLabelControl:
    """Tests for BindLabelControl."""

    def test_bind_label_set_value(self, wx_app):
        """Test setting label value from observable."""
        frame = wx.Frame(None)
        label = wx.StaticText(frame, label="initial")
        obs = Observable[str](initial="test value")

        BindLabelControl(label, obs)

        assert label.GetLabel() == "test value"
        frame.Destroy()

    def test_bind_label_clear(self, wx_app):
        """Test clearing label."""
        frame = wx.Frame(None)
        label = wx.StaticText(frame, label="initial")
        obs = Observable[str](initial="test")

        binding = BindLabelControl(label, obs)
        binding.clear()

        assert label.GetLabel() == "initial"
        frame.Destroy()


class TestBindValueControl:
    """Tests for BindValueControl."""

    def test_bind_textctrl_set_value(self, wx_app):
        """Test setting TextCtrl value from observable."""
        frame = wx.Frame(None)
        text = wx.TextCtrl(frame)
        obs = Observable[str](initial="hello")

        BindValueControl(text, obs)

        assert text.GetValue() == "hello"
        frame.Destroy()

    def test_bind_textctrl_observable_update(self, wx_app):
        """Test TextCtrl updates when observable changes."""
        frame = wx.Frame(None)
        text = wx.TextCtrl(frame)
        obs = Observable[str]()

        BindValueControl(text, obs)
        obs.set_value("updated")

        assert text.GetValue() == "updated"
        frame.Destroy()

    def test_bind_spinctrl_set_value(self, wx_app):
        """Test setting SpinCtrl value from observable."""
        frame = wx.Frame(None)
        spin = wx.SpinCtrl(frame, min=0, max=100)
        obs = Observable[int](initial=42)

        BindValueControl(spin, obs)

        assert spin.GetValue() == 42
        frame.Destroy()

    def test_bind_checkbox_set_value(self, wx_app):
        """Test setting CheckBox value from observable."""
        frame = wx.Frame(None)
        checkbox = wx.CheckBox(frame)
        obs = Observable[bool](initial=True)

        BindValueControl(checkbox, obs)

        assert checkbox.GetValue() is True
        frame.Destroy()

    def test_bind_checkbox_false(self, wx_app):
        """Test CheckBox with False value."""
        frame = wx.Frame(None)
        checkbox = wx.CheckBox(frame)
        obs = Observable[bool](initial=False)

        BindValueControl(checkbox, obs)

        assert checkbox.GetValue() is False
        frame.Destroy()


class TestBindSelectionControl:
    """Tests for BindSelectionControl."""

    def test_bind_choice_set_value(self, wx_app):
        """Test setting Choice value from observable."""
        frame = wx.Frame(None)
        choice = wx.Choice(frame, choices=["Option A", "Option B", "Option C"])
        obs = Observable[str](initial="Option B")

        BindSelectionControl(choice, obs)

        assert choice.GetStringSelection() == "Option B"
        frame.Destroy()

    def test_bind_choice_observable_update(self, wx_app):
        """Test Choice updates when observable changes."""
        frame = wx.Frame(None)
        choice = wx.Choice(frame, choices=["A", "B", "C"])
        obs = Observable[str]()

        BindSelectionControl(choice, obs)
        obs.set_value("C")

        assert choice.GetStringSelection() == "C"
        frame.Destroy()

    def test_bind_choice_invalid_value(self, wx_app):
        """Test Choice with invalid value."""
        frame = wx.Frame(None)
        choice = wx.Choice(frame, choices=["A", "B"])
        obs = Observable[str](initial="Invalid")

        BindSelectionControl(choice, obs)

        assert choice.GetSelection() == wx.NOT_FOUND
        frame.Destroy()


class TestAbstractModel:
    """Tests for AbstractModel."""

    def test_model_bind_control(self, wx_app):
        """Test binding control to model."""
        class TestModel(AbstractModel):
            name = Observable[str]()

        frame = wx.Frame(None)
        text = wx.TextCtrl(frame)

        model = TestModel()
        model.bind_control(text, model.name)
        model.name.set_value("test")

        assert text.GetValue() == "test"
        frame.Destroy()

    def test_model_bind_controls(self, wx_app):
        """Test binding multiple controls."""
        class TestModel(AbstractModel):
            name = Observable[str]()
            age = Observable[int]()

        frame = wx.Frame(None)
        name_text = wx.TextCtrl(frame)
        age_spin = wx.SpinCtrl(frame, min=0, max=100)

        model = TestModel()
        model.bind_controls(name=name_text, age=age_spin)
        model.name.set_value("John")
        model.age.set_value(30)

        assert name_text.GetValue() == "John"
        assert age_spin.GetValue() == 30
        frame.Destroy()
