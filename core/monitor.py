"""
Otomatik yeniden bağlanma monitörü.
"""
import threading
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional, Tuple

from core.auth import AuthService

if TYPE_CHECKING:
    from core.history import ConnectionHistory
    from core.notifier import NotificationService
    from core.settings import Settings


class ReconnectMonitor:
    """
    Arka planda internet bağlantısını izler; kopma durumunda
    AuthService üzerinden otomatik yeniden giriş yapar.

    Opsiyonel olarak:
    - Sistem bildirimleri gönderir (NotificationService)
    - Yeniden bağlanma olaylarını kaydeder (ConnectionHistory)
    """

    def __init__(
        self,
        auth_service: AuthService,
        history: Optional["ConnectionHistory"] = None,
        notifier: Optional["NotificationService"] = None,
        settings: Optional["Settings"] = None,
    ) -> None:
        self._auth = auth_service
        self._history = history
        self._notifier = notifier
        self._settings = settings
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._credentials: Optional[Tuple[str, str]] = None
        self._credentials_lock = threading.Lock()
        self._interval: int = 15
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_reconnect_attempt: Optional[Callable[[str], None]] = None

    @property
    def is_running(self) -> bool:
        """Monitor thread'inin çalışıp çalışmadığını döndürür."""
        return self._thread is not None and self._thread.is_alive()

    def start(self, tc: str, sifre: str, interval: int = 15) -> None:
        """
        Monitörü başlatır.

        Args:
            tc: Yeniden girişte kullanılacak TC kimlik numarası.
            sifre: Yeniden girişte kullanılacak şifre.
            interval: Kontrol aralığı (saniye).
        """
        if self.is_running:
            return
        with self._credentials_lock:
            self._credentials = (tc, sifre)
        self._interval = interval
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Monitörü durdurur (thread sonraki döngüde sonlanır)."""
        self._stop_event.set()

    def _notify_enabled(self) -> bool:
        """Bildirimler etkin mi?"""
        return self._notifier is not None and (
            self._settings is None or self._settings.get("notifications_enabled")
        )

    def _run(self) -> None:
        """Monitör döngüsü — arka plan thread'inde çalışır."""
        while not self._stop_event.wait(self._interval):
            try:
                if not self._auth.check_internet():
                    drop_time = datetime.now()
                    attempt_count = [0]

                    self._notify_status("Bağlantı kesildi, yeniden giriş yapılıyor...")

                    if self._notify_enabled():
                        self._notifier.send(
                            "GSBWIFI Bypass",
                            "Bağlantı kesildi, yeniden bağlanılıyor..."
                        )

                    with self._credentials_lock:
                        creds = self._credentials

                    if not creds:
                        continue

                    def on_attempt(n: int, msg: str) -> None:
                        attempt_count[0] = n
                        self._notify_attempt(f"Deneme {n}: {msg}")

                    def on_success(n: int) -> None:
                        duration = (datetime.now() - drop_time).total_seconds()
                        self._notify_status(f"Yeniden bağlandı ({n}. denemede)")

                        if self._notify_enabled():
                            self._notifier.send(
                                "GSBWIFI Bypass",
                                f"Yeniden bağlandı! ({n}. denemede, {duration:.0f}sn)"
                            )

                        if self._history and (
                            self._settings is None
                            or self._settings.get("history_enabled")
                        ):
                            self._history.add_reconnect(
                                attempts=n,
                                duration=duration,
                                success=True,
                            )

                    self._auth.login(
                        creds[0],
                        creds[1],
                        on_attempt=on_attempt,
                        on_success=on_success,
                    )

            except Exception as e:
                # Thread'in sessizce ölmesini önle; hatayı bildir
                self._notify_status(f"Monitor hatası: {e}")

    def _notify_status(self, msg: str) -> None:
        if self.on_status_change:
            self.on_status_change(msg)

    def _notify_attempt(self, msg: str) -> None:
        if self.on_reconnect_attempt:
            self.on_reconnect_attempt(msg)
