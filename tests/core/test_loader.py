import pytest

from helpers.loader import Loader


class TestLoader:
    """Tests for Loader class."""

    def test_initial_state(self):
        """Test initial loading state is False."""
        # Reset state
        Loader._queue.set_value([])
        Loader._update_loading_state()

        assert Loader.loading.get_value() is False

    def test_cursor_wait_sets_loading(self):
        """Test cursor_wait sets loading to True."""
        Loader._queue.set_value([])
        Loader._update_loading_state()

        with Loader.cursor_wait():
            assert Loader.loading.get_value() is True

        assert Loader.loading.get_value() is False

    def test_nested_cursor_wait(self):
        """Test nested cursor_wait maintains loading state."""
        Loader._queue.set_value([])
        Loader._update_loading_state()

        with Loader.cursor_wait():
            assert Loader.loading.get_value() is True
            with Loader.cursor_wait():
                assert Loader.loading.get_value() is True
            # Still loading because outer context is active
            assert Loader.loading.get_value() is True

        assert Loader.loading.get_value() is False

    def test_cursor_wait_exception_cleanup(self):
        """Test cursor_wait cleans up on exception."""
        Loader._queue.set_value([])
        Loader._update_loading_state()

        try:
            with Loader.cursor_wait():
                assert Loader.loading.get_value() is True
                raise ValueError("test error")
        except ValueError:
            pass

        assert Loader.loading.get_value() is False
