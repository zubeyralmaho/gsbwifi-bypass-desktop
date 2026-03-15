"""
Platform bağımsız sistem bildirimi servisi.
subprocess üzerinden native OS komutlarını kullanır; ek paket gerektirmez.
"""
import platform
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.settings import Settings


class NotificationService:
    """
    İşletim sisteminin native bildirim mekanizmasını kullanan servis.

    - macOS: osascript (AppleScript)
    - Linux: notify-send (libnotify)
    - Windows: PowerShell NotifyIcon

    Bildirimler non-critical'dır; herhangi bir hata sessizce yoksayılır.
    """

    APP_NAME = "GSBWIFI Bypass"

    def __init__(self, settings: "Settings") -> None:
        self._settings = settings

    def send(self, title: str, message: str) -> None:
        """
        Sistem bildirimi gönderir.

        Bildirimler ayardan devre dışı bırakılmışsa sessizce döner.

        Args:
            title: Bildirim başlığı.
            message: Bildirim metni.
        """
        if not self._settings.get("notifications_enabled"):
            return
        self._dispatch(title, message)

    def _dispatch(self, title: str, message: str) -> None:
        """Platform'a göre uygun bildirim komutunu çalıştırır."""
        system = platform.system()
        try:
            if system == "Darwin":
                self._notify_macos(title, message)
            elif system == "Linux":
                self._notify_linux(title, message)
            else:
                self._notify_windows(title, message)
        except Exception:
            pass  # Bildirim başarısız olursa uygulamayı etkileme

    def _notify_macos(self, title: str, message: str) -> None:
        # Tırnak işaretlerini temizle (AppleScript enjeksiyonu önle)
        safe_title = title.replace('"', "'")
        safe_message = message.replace('"', "'")
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{safe_message}" with title "{safe_title}"'],
            timeout=3,
            check=False,
            capture_output=True,
        )

    def _notify_linux(self, title: str, message: str) -> None:
        subprocess.run(
            ["notify-send", "--app-name", self.APP_NAME, title, message],
            timeout=3,
            check=False,
            capture_output=True,
        )

    def _notify_windows(self, title: str, message: str) -> None:
        safe_title = title.replace('"', "'")
        safe_message = message.replace('"', "'")
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Information; "
            "$n.Visible = $true; "
            f'$n.ShowBalloonTip(4000, "{safe_title}", "{safe_message}", '
            "[System.Windows.Forms.ToolTipIcon]::Info); "
            "Start-Sleep -Milliseconds 4500; $n.Dispose()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            timeout=8,
            check=False,
            capture_output=True,
        )
