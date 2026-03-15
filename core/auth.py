import time
import threading
import requests


class AuthService:
    LOGIN_URL = "https://wifi.gsb.gov.tr/j_spring_security_check"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    def __init__(self):
        self._stop_event = threading.Event()
        self._session = None

    def login(self, tc, sifre, on_attempt=None, on_success=None, on_error=None, interval=0.3):
        self._stop_event.clear()
        self._session = requests.Session()
        attempts = 0
        payload = {"j_username": tc, "j_password": sifre}

        while not self._stop_event.is_set():
            attempts += 1
            try:
                resp = self._session.post(
                    self.LOGIN_URL,
                    data=payload,
                    headers=self.HEADERS,
                    timeout=2,
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
            except requests.exceptions.RequestException as e:
                if on_attempt:
                    on_attempt(attempts, f"Ağ hatası: {e}")

            time.sleep(interval)

        return False

    def stop(self):
        self._stop_event.set()

    def check_internet(self):
        try:
            resp = requests.get("http://clients3.google.com/generate_204", timeout=3)
            return resp.status_code == 204
        except requests.RequestException:
            return False
