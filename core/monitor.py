import threading


class ReconnectMonitor:
    def __init__(self, auth_service):
        self._auth = auth_service
        self._stop_event = threading.Event()
        self._thread = None
        self._credentials = None
        self._interval = 15
        self.on_status_change = None
        self.on_reconnect_attempt = None

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self, tc, sifre, interval=15):
        if self.is_running:
            return
        self._credentials = (tc, sifre)
        self._interval = interval
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.wait(self._interval):
            if not self._auth.check_internet():
                self._notify_status("Bağlantı kesildi, yeniden giriş yapılıyor...")
                self._auth.login(
                    self._credentials[0],
                    self._credentials[1],
                    on_attempt=lambda n, msg: self._notify_attempt(f"Deneme {n}: {msg}"),
                    on_success=lambda n: self._notify_status(f"Yeniden bağlandı ({n}. denemede)"),
                )

    def _notify_status(self, msg):
        if self.on_status_change:
            self.on_status_change(msg)

    def _notify_attempt(self, msg):
        if self.on_reconnect_attempt:
            self.on_reconnect_attempt(msg)
