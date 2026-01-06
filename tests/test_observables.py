import pytest

from helpers.observables import Observable, ObservableList, ObservableLazyList, CallbackEvent


class TestObservable:
    def test_observable_creation(self):
        obs = Observable(initial=10)
        assert obs._value == 10
        assert obs._last_value == 10

    def test_observable_get_value(self):
        obs = Observable(initial=5)
        assert obs.get_value() == 5

    def test_observable_set_value(self):
        obs = Observable()
        obs.set_value(20)
        assert obs.get_value() == 20

    def test_observable_callbacks(self):
        obs = Observable()
        called = []

        def callback(value):
            called.append(True)

        obs.subscribe(callback, CallbackEvent.AFTER_CHANGE)
        obs.set_value(30)
        assert len(called) == 1


class TestObservableList:
    def test_observable_list_creation(self):
        obs_list = ObservableList([1, 2, 3])
        assert obs_list.get_value() == [1, 2, 3]

    def test_observable_list_append(self):
        obs_list = ObservableList()
        obs_list.append(4)
        assert obs_list.get_value() == [4]

    def test_observable_list_extend(self):
        obs_list = ObservableList([1])
        obs_list.extend([2, 3])
        assert obs_list.get_value() == [1, 2, 3]

    def test_observable_list_remove(self):
        obs_list = ObservableList([1, 2, 3])
        obs_list.remove(2)
        assert obs_list.get_value() == [1, 3]


class TestObservableLazyList:
    def test_observable_lazy_list_creation(self):
        def loader():
            return [1, 2, 3]

        obs_lazy = ObservableLazyList(loader)
        assert not obs_lazy.is_loaded
        assert obs_lazy.get_value() == [1, 2, 3]
        assert obs_lazy.is_loaded

    def test_observable_lazy_list_refresh(self):
        call_count = [0]
        def loader():
            call_count[0] += 1
            return [call_count[0]]

        obs_lazy = ObservableLazyList(loader)
        obs_lazy.get_value()  # loads [1]
        obs_lazy.refresh()
        obs_lazy.get_value()  # loads [2]
        assert obs_lazy.get_value() == [2]
