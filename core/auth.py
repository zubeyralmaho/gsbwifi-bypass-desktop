"""
GSBWIFI kimlik doğrulama servisi.
"""
import time
import threading
from typing import Callable, Optional

import requests

from core.constants import (
    LOGIN_URL,
    LOGIN_HEADERS,
    DEFAULT_LOGIN_INTERVAL,
    LOGIN_REQUEST_TIMEOUT,
    INTERNET_CHECK_TIMEOUT,
)


class AuthService:
    """GSBWIFI captive portal'ına login işlemlerini yönetir."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._session: Optional[requests.Session] = None
        self._lock = threading.Lock()
        self._is_running = False

    def login(
        self,
        tc: str,
        sifre: str,
        on_attempt: Optional[Callable[[int, str], None]] = None,
        on_success: Optional[Callable[[int], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        interval: float = DEFAULT_LOGIN_INTERVAL,
    ) -> bool:
        """
        GSBWIFI'ye tekrarlayan POST istekleri göndererek login yapar.

        Eş zamanlı çağrı koruması vardır: ikinci bir login denemesi önceki
        bitmeden sessizce iptal edilir.

        Args:
            tc: 11 haneli TC kimlik numarası.
            sifre: Kullanıcı şifresi.
            on_attempt: Her denemede çağrılan callback(deneme_no, mesaj).
            on_success: Başarılı girişte çağrılan callback(deneme_no).
            on_error: Kritik hata durumunda çağrılan callback(mesaj).
            interval: Denemeler arası bekleme süresi (saniye).

        Returns:
            True başarılı login, False durduruldu/hata.
        """
        with self._lock:
            if self._is_running:
                return False
            self._is_running = True

        self._stop_event.clear()
        self._session = requests.Session()
        attempts = 0
        payload = {"j_username": tc, "j_password": sifre}

        try:
            while not self._stop_event.is_set():
                attempts += 1
                try:
                    resp = self._session.post(
                        LOGIN_URL,
                        data=payload,
                        headers=LOGIN_HEADERS,
                        timeout=LOGIN_REQUEST_TIMEOUT,
                        allow_redirects=False,
                    )
                    if resp.status_code == 302 and "Location" in resp.headers:
                        if on_success:
                            on_success(attempts)
                        return True
                    if resp.status_code == 200 and "giriş başarılı" in resp.text.lower():
                        if on_success:
                            on_success(attempts)
                        return True
                    if on_attempt:
                        on_attempt(attempts, "Giriş onaylanmadı")
                except requests.exceptions.Timeout:
                    if on_attempt:
                        on_attempt(attempts, "Timeout")
                except requests.exceptions.ConnectionError:
                    if on_attempt:
                        on_attempt(attempts, "Bağlantı hatası")
                except requests.exceptions.RequestException as e:
                    if on_attempt:
                        on_attempt(attempts, f"Ağ hatası: {e}")

                time.sleep(interval)
        finally:
            with self._lock:
                self._is_running = False

        return False

    def stop(self) -> None:
        """Devam eden login döngüsünü durdurur."""
        self._stop_event.set()

    def check_internet(self) -> bool:
        """İnternet bağlantısını kontrol eder (HTTP 204 ile)."""
        try:
            resp = requests.get(
                "http://clients3.google.com/generate_204",
                timeout=INTERNET_CHECK_TIMEOUT,
            )
            return resp.status_code == 204
        except requests.RequestException:
            return False
