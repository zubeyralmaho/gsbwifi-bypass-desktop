"""
Uygulama ayarlarının yönetimi.
Kimlik bilgileri OS'un güvenli anahtar zincirinde (keyring) saklanır;
diğer ayarlar platform uygun dizinde JSON olarak tutulur.
"""
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

_KEYRING_SERVICE = "gsbwifi-bypass"


def get_data_dir() -> Path:
    """Platform'a uygun uygulama veri dizinini döndürür ve oluşturur."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    data_dir = base / "GSBWiFi"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class Settings:
    """
    JSON tabanlı uygulama ayar deposu.

    Kimlik bilgileri (TC/şifre), keyring kütüphanesi mevcutsa OS'un
    güvenli deposunda saklanır. Yoksa JSON'da düz metin olarak tutulur
    ve bir uyarı gösterilir.
    """

    DEFAULTS: dict[str, Any] = {
        "remember_credentials": False,
        "saved_tc": "",
        "saved_password": "",  # keyring yoksa fallback olarak kullanılır
        "auto_reconnect": False,
        "reconnect_interval": 15,
        "appearance_mode": "System",
        "login_interval": 0.3,
        "notifications_enabled": True,
        "history_enabled": True,
    }

    def __init__(self) -> None:
        self._path = get_data_dir() / "settings.json"
        self._data: dict[str, Any] = dict(self.DEFAULTS)
        self.load()
        if not _KEYRING_AVAILABLE:
            print(
                "[Uyarı] 'keyring' paketi bulunamadı. Kimlik bilgileri düz "
                "metin olarak saklanacak. Güvenlik için: pip install keyring",
                file=sys.stderr,
            )

    # ------------------------------------------------------------------
    # JSON yükleme / kaydetme
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Ayarları JSON dosyasından yükler; hata varsa varsayılanları kullanır."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for key in self.DEFAULTS:
                if key in saved:
                    self._data[key] = saved[key]
        except json.JSONDecodeError as e:
            print(f"[Uyarı] Ayar dosyası okunamadı (JSON hatası): {e}", file=sys.stderr)
        except OSError as e:
            print(f"[Uyarı] Ayar dosyası açılamadı: {e}", file=sys.stderr)

    def save(self) -> None:
        """Ayarları JSON dosyasına kaydeder."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Hata] Ayarlar kaydedilemedi: {e}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Genel get / set
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any:
        """Ayar değerini döndürür; bulunamazsa varsayılanı döner."""
        return self._data.get(key, self.DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        """Ayar değerini günceller ve anında diske kaydeder."""
        self._data[key] = value
        self.save()

    # ------------------------------------------------------------------
    # Kimlik bilgisi yönetimi (keyring destekli)
    # ------------------------------------------------------------------

    def save_credentials(self, tc: str, password: str) -> None:
        """TC kimliği ve şifreyi güvenli depoya kaydeder."""
        self._data["saved_tc"] = tc
        if _KEYRING_AVAILABLE:
            try:
                keyring.set_password(_KEYRING_SERVICE, tc, password)
                # JSON'da şifreyi saklamaya gerek yok; TC yeterli
                self._data["saved_password"] = ""
            except Exception as e:
                print(f"[Uyarı] Keyring'e yazılamadı: {e}", file=sys.stderr)
                self._data["saved_password"] = password
        else:
            self._data["saved_password"] = password
        self.save()

    def load_password(self, tc: str) -> Optional[str]:
        """Verilen TC için kaydedilmiş şifreyi döndürür."""
        if _KEYRING_AVAILABLE and tc:
            try:
                pwd = keyring.get_password(_KEYRING_SERVICE, tc)
                if pwd is not None:
                    return pwd
            except Exception as e:
                print(f"[Uyarı] Keyring'den okunamadı: {e}", file=sys.stderr)
        # Fallback: JSON'daki düz metin
        return self._data.get("saved_password") or None

    def clear_credentials(self) -> None:
        """Kayıtlı kimlik bilgilerini temizler."""
        tc = self._data.get("saved_tc", "")
        if _KEYRING_AVAILABLE and tc:
            try:
                keyring.delete_password(_KEYRING_SERVICE, tc)
            except Exception:
                pass
        self._data["saved_tc"] = ""
        self._data["saved_password"] = ""
        self._data["remember_credentials"] = False
        self.save()
