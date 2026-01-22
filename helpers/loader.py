from contextlib import contextmanager

from helpers.observables import Observable


class Loader:
    _queue: Observable[list] = Observable([])
    loading: Observable[bool] = Observable(False)

    @classmethod
    def _update_loading_state(cls):
        """Update loading state based on queue length"""
        cls.loading(len(cls._queue()) > 0)

    @classmethod
    @contextmanager
    def cursor_wait(cls):
        """Context manager to show wait cursor during operations"""
        token = object()  # Unique token for this operation

        # Add token to queue
        current_queue = cls._queue()
        current_queue.append(token)
        cls._queue(current_queue)
        cls._update_loading_state()

        try:
            yield
        finally:
            # Remove token from queue
            current_queue = cls._queue()
            if token in current_queue:
                current_queue.remove(token)
                cls._queue(current_queue)
                cls._update_loading_state()