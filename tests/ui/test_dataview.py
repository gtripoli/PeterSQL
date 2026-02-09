import pytest
from dataclasses import dataclass

from helpers.dataview import ColumnField, AbstractBaseDataModel


@dataclass
class MockItem:
    """Mock item for testing."""
    name: str
    value: int
    active: bool = True


class TestColumnField:
    """Tests for ColumnField."""

    def test_get_value_simple(self):
        """Test getting simple attribute value."""
        field = ColumnField(attr="name")
        item = MockItem(name="test", value=42)

        assert field.get_value(item) == "test"

    def test_get_value_with_transform(self):
        """Test getting value with transform function."""
        def double(x):
            return x * 2
        field = ColumnField(attr="value", transform=double)
        item = MockItem(name="test", value=21)

        assert field.get_value(item) == 42

    def test_get_value_with_lambda_item_access(self):
        """Test lambda with item access."""
        field = ColumnField(attr="value", transform=lambda item, val: f"{item.name}: {val}")
        item = MockItem(name="test", value=42)

        assert field.get_value(item) == "test: 42"

    def test_get_value_missing_attr(self):
        """Test getting missing attribute returns None."""
        field = ColumnField(attr="missing")
        item = MockItem(name="test", value=42)

        assert field.get_value(item) is None

    def test_has_value_true(self):
        """Test has_value returns True for existing value."""
        field = ColumnField(attr="name")
        item = MockItem(name="test", value=42)

        assert field.has_value(item) is True

    def test_has_value_false(self):
        """Test has_value returns False for None value."""
        field = ColumnField(attr="missing")
        item = MockItem(name="test", value=42)

        assert field.has_value(item) is False


class ConcreteDataModel(AbstractBaseDataModel):
    """Concrete implementation for testing."""

    def set_observable(self, observable):
        self._observable = observable


class TestAbstractBaseDataModel:
    """Tests for AbstractBaseDataModel."""

    def test_load(self):
        """Test loading data."""
        model = ConcreteDataModel()
        data = [MockItem("a", 1), MockItem("b", 2)]

        model.load(data)

        assert len(model.data) == 2
        assert model.data[0].name == "a"

    def test_append(self):
        """Test appending data."""
        model = ConcreteDataModel()
        model.load([MockItem("a", 1)])

        index = model.append(MockItem("b", 2))

        assert index == 1
        assert len(model.data) == 2

    def test_insert(self):
        """Test inserting data."""
        model = ConcreteDataModel()
        model.load([MockItem("a", 1), MockItem("c", 3)])

        index = model.insert(MockItem("b", 2), 1)

        assert index == 1
        assert model.data[1].name == "b"

    def test_remove(self):
        """Test removing data."""
        model = ConcreteDataModel()
        item_a = MockItem("a", 1)
        item_b = MockItem("b", 2)
        model.load([item_a, item_b])

        index = model.remove(item_a)

        assert index == 0
        assert len(model.data) == 1
        assert model.data[0].name == "b"

    def test_pop(self):
        """Test popping data."""
        model = ConcreteDataModel()
        item_a = MockItem("a", 1)
        item_b = MockItem("b", 2)
        model.load([item_a, item_b])

        index = model.pop(item_b)

        assert index == 1
        assert len(model.data) == 1

    def test_clear(self):
        """Test clearing data."""
        model = ConcreteDataModel()
        model.load([MockItem("a", 1), MockItem("b", 2)])

        model.clear()

        assert len(model.data) == 0

    def test_get_data_by_row(self):
        """Test getting data by row index."""
        model = ConcreteDataModel()
        item = MockItem("test", 42)
        model.load([item])

        assert model.get_data_by_row(0) == item

    def test_set_data_by_row(self):
        """Test setting data by row index."""
        model = ConcreteDataModel()
        model.load([MockItem("old", 1)])
        new_item = MockItem("new", 2)

        model.set_data_by_row(0, new_item)

        assert model.data[0].name == "new"

    def test_get_item_by_name(self):
        """Test getting item by name."""
        model = ConcreteDataModel()
        item_a = MockItem("a", 1)
        item_b = MockItem("b", 2)
        model.load([item_a, item_b])

        result = model.get_item_by_name("b")

        assert result == item_b

    def test_get_item_by_name_not_found(self):
        """Test getting item by name when not found."""
        model = ConcreteDataModel()
        model.load([MockItem("a", 1)])

        result = model.get_item_by_name("missing")

        assert result is None

    def test_get_item_by_filters(self):
        """Test getting item by filters."""
        model = ConcreteDataModel()
        item_a = MockItem("a", 1, active=True)
        item_b = MockItem("b", 2, active=False)
        model.load([item_a, item_b])

        result = model.get_item_by_filters(active=False)

        assert result == item_b

    def test_move(self):
        """Test moving data."""
        model = ConcreteDataModel()
        item_a = MockItem("a", 1)
        item_b = MockItem("b", 2)
        model.load([item_a, item_b])

        model.move(item_a, 0, 1)

        assert model.data[0].name == "b"
        assert model.data[1].name == "a"

    def test_filter(self):
        """Test filtering data."""
        model = ConcreteDataModel()
        model.load([MockItem("a", 1), MockItem("b", 2), MockItem("c", 3)])

        filtered = [MockItem("b", 2)]
        model.filter(filtered)

        assert len(model.data) == 1
        assert model.data[0].name == "b"
