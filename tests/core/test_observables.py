import pytest

from helpers.observables import Observable, ObservableList, CallbackEvent, ValueState


class TestObservable:
    """Tests for Observable class."""

    def test_observable_initial_value(self):
        """Test observable with initial value."""
        obs = Observable[int](initial=42)
        assert obs.get_value() == 42

    def test_observable_no_initial_value(self):
        """Test observable without initial value."""
        obs = Observable[str]()
        assert obs.get_value() is None

    def test_observable_set_value(self):
        """Test setting observable value."""
        obs = Observable[str]()
        obs.set_value("hello")
        assert obs.get_value() == "hello"

    def test_observable_state_undefined(self):
        """Test observable state when undefined."""
        obs = Observable[int]()
        assert obs.state == ValueState.UNDEFINED

    def test_observable_state_defined(self):
        """Test observable state when defined."""
        obs = Observable[int](initial=10)
        assert obs.state == ValueState.DEFINED

    def test_observable_state_empty(self):
        """Test observable state when empty."""
        obs = Observable[str](initial="")
        assert obs.state == ValueState.EMPTY

    def test_observable_is_empty_none(self):
        """Test is_empty with None value."""
        obs = Observable[str](initial=None)
        assert obs.is_empty is True

    def test_observable_is_empty_string(self):
        """Test is_empty with empty string."""
        obs = Observable[str](initial="")
        assert obs.is_empty is True

    def test_observable_is_empty_list(self):
        """Test is_empty with empty list."""
        obs = Observable[list](initial=[])
        assert obs.is_empty is True

    def test_observable_not_empty(self):
        """Test is_empty with value."""
        obs = Observable[str](initial="hello")
        assert obs.is_empty is False

    def test_observable_subscribe_after_change(self):
        """Test subscribe with AFTER_CHANGE event."""
        obs = Observable[int](initial=0)
        results = []

        def callback(value):
            results.append(value)

        obs.subscribe(callback, CallbackEvent.AFTER_CHANGE)
        obs.set_value(1)
        obs.set_value(2)

        assert results == [0, 1, 2]

    def test_observable_subscribe_before_change(self):
        """Test subscribe with BEFORE_CHANGE event."""
        obs = Observable[int](initial=0)
        results = []

        def callback(value):
            results.append(value)

        obs.subscribe(callback, CallbackEvent.BEFORE_CHANGE)
        obs.set_value(1)

        assert results == [0, 0]

    def test_observable_unsubscribe(self):
        """Test unsubscribe from observable."""
        obs = Observable[int](initial=0)
        results = []

        def callback(value):
            results.append(value)

        obs.subscribe(callback, CallbackEvent.AFTER_CHANGE)
        obs.unsubscribe(callback, CallbackEvent.AFTER_CHANGE)
        obs.set_value(1)

        assert results == [0]

    def test_observable_set_initial(self):
        """Test set_initial method."""
        obs = Observable[int]()
        obs.set_initial(100)
        assert obs.get_value() == 100

    def test_observable_no_callback_on_same_value(self):
        """Test that callback is not called when value doesn't change."""
        obs = Observable[int](initial=5)
        results = []

        def callback(value):
            results.append(value)

        obs.subscribe(callback, CallbackEvent.AFTER_CHANGE)
        results.clear()
        obs.set_value(5)

        assert results == []


class TestObservableList:
    """Tests for ObservableList class."""

    def test_observable_list_initial(self):
        """Test observable list with initial value."""
        obs = ObservableList[int](initial=[1, 2, 3])
        assert obs.get_value() == [1, 2, 3]

    def test_observable_list_append(self):
        """Test appending to observable list."""
        obs = ObservableList[int](initial=[1, 2])
        obs.append(3)
        assert obs.get_value() == [1, 2, 3]

    def test_observable_list_remove(self):
        """Test removing from observable list."""
        obs = ObservableList[int](initial=[1, 2, 3])
        obs.remove(2)
        assert obs.get_value() == [1, 3]

    def test_observable_list_clear(self):
        """Test clearing observable list."""
        obs = ObservableList[int](initial=[1, 2, 3])
        obs.clear()
        assert obs.get_value() == []

    def test_observable_list_iter(self):
        """Test iterating observable list."""
        obs = ObservableList[int](initial=[1, 2, 3])
        result = list(obs)
        assert result == [1, 2, 3]

    def test_observable_list_len(self):
        """Test length of observable list."""
        obs = ObservableList[int](initial=[1, 2, 3])
        assert len(obs) == 3

    def test_observable_list_getitem(self):
        """Test getitem on observable list."""
        obs = ObservableList[str](initial=["a", "b", "c"])
        assert obs[1] == "b"

    def test_observable_list_append_callback(self):
        """Test append triggers callback."""
        obs = ObservableList[int](initial=[])
        results = []

        def callback(value):
            results.append(value)

        obs.subscribe(callback, CallbackEvent.ON_APPEND)
        obs.append(42)

        assert 42 in results

    def test_observable_list_extend(self):
        """Test extending observable list."""
        obs = ObservableList[int](initial=[1])
        obs.extend([2, 3])
        assert obs.get_value() == [1, 2, 3]

    def test_observable_list_insert(self):
        """Test inserting into observable list."""
        obs = ObservableList[int](initial=[1, 3])
        obs.insert(1, 2)
        assert obs.get_value() == [1, 2, 3]

    def test_observable_list_pop(self):
        """Test popping from observable list."""
        obs = ObservableList[int](initial=[1, 2, 3])
        obs.pop()  # pop returns Self, not the value
        assert obs.get_value() == [1, 2]
