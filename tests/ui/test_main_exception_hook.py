import main

from main import PeterSQL


class TestPeterSQLExceptionHook:
    def test_on_exception_in_main_loop_logs_and_returns_true(self, monkeypatch):
        messages = []

        def fake_exception(message):
            messages.append(message)

        monkeypatch.setattr(main.logger, "exception", fake_exception)

        result = PeterSQL.OnExceptionInMainLoop(object())

        assert result is True
        assert messages == ["Unhandled exception raised inside wx main loop"]