import wx

from windows.views import SplashScreen

_TICK_MS = 50


class SplashController(SplashScreen):
    _MIN_DURATION = 1.5

    def __init__(self):
        super().__init__(None)
        self._timer = wx.Timer(self)
        self._tick_count = 0
        self._total_ticks = int(self._MIN_DURATION * 1000 / _TICK_MS)
        self._on_done = None
        self.Bind(wx.EVT_TIMER, self._on_tick)

    def start_close(self, on_done) -> None:
        self._on_done = on_done
        self._timer.Start(_TICK_MS)

    def _on_tick(self, event: wx.TimerEvent) -> None:
        self._tick_count += 1
        self.m_gauge1.SetValue(round(100 * self._tick_count / self._total_ticks))
        if self._tick_count >= self._total_ticks:
            self._timer.Stop()
            self.Destroy()
            self._on_done()
