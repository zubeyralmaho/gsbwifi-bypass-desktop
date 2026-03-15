"""
Cloudflare WARP CLI entegrasyonu.
"""
import os
import platform
import shutil
import subprocess
import glob as globmod
from typing import Callable, List, Optional, Tuple

from core.constants import (
    WARP_CONNECT_TIMEOUT,
    WARP_INSTALL_TIMEOUT,
    WarpStatus,
)


# macOS'ta warp-cli bilinen konumlar
_MACOS_WARP_PATHS = [
    "/usr/local/bin/warp-cli",
    "/Applications/Cloudflare WARP.app/Contents/Resources/warp-cli",
]

# Linux'ta bilinen konumlar
_LINUX_WARP_PATHS = [
    "/usr/bin/warp-cli",
    "/usr/local/bin/warp-cli",
]


class WarpService:
    """Cloudflare WARP CLI'yi sarar; kurulum, bağlantı ve durum sorgulama sağlar."""

    def __init__(self) -> None:
        self._warp_cli_path: Optional[str] = self._find_warp_cli()

    # ------------------------------------------------------------------
    # Durum sorgulama
    # ------------------------------------------------------------------

    def _find_warp_cli(self) -> Optional[str]:
        """warp-cli yürütülebilir dosyasını PATH'te ve bilinen konumlarda arar."""
        found = shutil.which("warp-cli")
        if found:
            return found

        system = platform.system()
        search_paths: List[str] = []
        if system == "Darwin":
            search_paths = _MACOS_WARP_PATHS
        elif system == "Linux":
            search_paths = _LINUX_WARP_PATHS

        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def is_installed(self) -> bool:
        """WARP CLI'nin kurulu olup olmadığını döndürür."""
        self._warp_cli_path = self._find_warp_cli()
        return self._warp_cli_path is not None

    def get_status(self) -> str:
        """
        Mevcut WARP bağlantı durumunu döndürür.

        Returns:
            WarpStatus değerlerinden biri (str olarak).
        """
        if not self.is_installed():
            return WarpStatus.NOT_INSTALLED
        try:
            result = subprocess.run(
                [self._warp_cli_path, "status"],
                capture_output=True,
                text=True,
                timeout=WARP_CONNECT_TIMEOUT,
            )
            if "Connected" in result.stdout:
                return WarpStatus.CONNECTED
            return WarpStatus.DISCONNECTED
        except subprocess.TimeoutExpired:
            return WarpStatus.UNKNOWN
        except OSError:
            return WarpStatus.UNKNOWN

    # ------------------------------------------------------------------
    # Bağlantı yönetimi
    # ------------------------------------------------------------------

    def _run_warp_command(
        self, *args: str, timeout: int = WARP_CONNECT_TIMEOUT
    ) -> Tuple[bool, str]:
        """
        Ortak WARP CLI komut çalıştırıcı.

        Args:
            *args: warp-cli'ye geçirilecek argümanlar (ör. "connect").
            timeout: Saniye cinsinden maksimum bekleme süresi.

        Returns:
            (başarı, mesaj) tuple'ı.
        """
        if not self.is_installed():
            return False, "WARP kurulu değil"
        try:
            result = subprocess.run(
                [self._warp_cli_path, *args],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, result.stderr.strip() or result.stdout.strip() or "Komut başarısız"
        except subprocess.TimeoutExpired:
            return False, "Komut zaman aşımına uğradı"
        except OSError as e:
            return False, str(e)

    def connect(self) -> Tuple[bool, str]:
        """WARP bağlantısını başlatır."""
        success, msg = self._run_warp_command("connect")
        if success:
            return True, "WARP bağlantısı başlatıldı"
        return False, msg or "Bağlantı başarısız"

    def disconnect(self) -> Tuple[bool, str]:
        """WARP bağlantısını keser."""
        success, msg = self._run_warp_command("disconnect")
        if success:
            return True, "WARP bağlantısı kesildi"
        return False, msg or "Bağlantı kesilemedi"

    # ------------------------------------------------------------------
    # Kurulum
    # ------------------------------------------------------------------

    def auto_install(
        self, on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        Platforma göre WARP'ı otomatik kurar.

        Args:
            on_output: Kurulum çıktısı için satır bazlı callback.

        Returns:
            (başarı, mesaj) tuple'ı.
        """
        system = platform.system()
        try:
            if system == "Windows":
                success, msg = self._run_install(
                    ["winget", "install", "-e", "--id", "Cloudflare.Warp",
                     "--accept-source-agreements", "--accept-package-agreements"],
                    on_output,
                )
                if success:
                    self._warp_cli_path = self._find_warp_cli()
                return success, "WARP başarıyla kuruldu" if success else msg

            if system == "Darwin":
                return self._install_macos(on_output)

            return self._install_linux(on_output)

        except Exception as e:
            return False, f"Kurulum hatası: {e}"

    def _install_macos(
        self, on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """Homebrew cask aracılığıyla macOS'a WARP kurar."""
        if not shutil.which("brew"):
            return False, "Homebrew bulunamadı. Lütfen önce Homebrew kurun: https://brew.sh"

        success, msg = self._run_install(
            ["brew", "install", "--cask", "cloudflare-warp"],
            on_output,
        )
        if not success and "already installed" not in msg.lower():
            return False, msg

        pkg_files = (
            globmod.glob("/opt/homebrew/Caskroom/cloudflare-warp/*/Cloudflare_WARP_*.pkg")
            + globmod.glob("/usr/local/Caskroom/cloudflare-warp/*/Cloudflare_WARP_*.pkg")
        )
        if not pkg_files:
            return False, "WARP .pkg dosyası bulunamadı. brew indirimi başarısız olmuş olabilir."

        pkg_path = sorted(pkg_files)[-1]
        if on_output:
            on_output(f"WARP paketi kuruluyor: {os.path.basename(pkg_path)}")

        success, msg = self._run_install(
            ["osascript", "-e",
             f'do shell script "installer -pkg \'{pkg_path}\' -target /" with administrator privileges'],
            on_output,
        )
        if success:
            self._warp_cli_path = self._find_warp_cli()
            return True, "WARP başarıyla kuruldu"
        return False, msg

    def _install_linux(
        self, on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """apt/dnf/yum aracılığıyla Linux'a WARP kurar."""
        if shutil.which("apt-get"):
            cmds = [
                ["sudo", "mkdir", "-p", "--mode=0755", "/usr/share/keyrings"],
                ["bash", "-c",
                 "curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg "
                 "| sudo gpg --yes --dearmor --output "
                 "/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg"],
                ["bash", "-c",
                 'echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] '
                 'https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" '
                 '| sudo tee /etc/apt/sources.list.d/cloudflare-client.list'],
                ["sudo", "apt-get", "update"],
                ["sudo", "apt-get", "install", "-y", "cloudflare-warp"],
            ]
            pm = "apt"
        elif shutil.which("dnf"):
            cmds = [
                ["sudo", "rpm", "-ivh", "https://pkg.cloudflareclient.com/cloudflare-release-el8.rpm"],
                ["sudo", "dnf", "install", "-y", "cloudflare-warp"],
            ]
            pm = "dnf"
        elif shutil.which("yum"):
            cmds = [
                ["sudo", "rpm", "-ivh", "https://pkg.cloudflareclient.com/cloudflare-release-el8.rpm"],
                ["sudo", "yum", "install", "-y", "cloudflare-warp"],
            ]
            pm = "yum"
        else:
            return False, "Desteklenen paket yöneticisi bulunamadı (apt/dnf/yum)"

        for cmd in cmds:
            success, msg = self._run_install(cmd, on_output)
            if not success:
                return False, msg

        self._warp_cli_path = self._find_warp_cli()
        return True, f"WARP başarıyla kuruldu ({pm})"

    def _run_install(
        self,
        cmd: List[str],
        on_output: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """Tek bir kurulum komutunu çalıştırır ve çıktıyı aktarır."""
        try:
            if on_output:
                on_output(f"Çalıştırılıyor: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=WARP_INSTALL_TIMEOUT,
            )
            if on_output and result.stdout:
                for line in result.stdout.strip().split("\n")[-3:]:
                    if line.strip():
                        on_output(line.strip())
            if result.returncode == 0:
                return True, "Komut başarılı"
            err = result.stderr.strip() or result.stdout.strip() or "Bilinmeyen hata"
            if on_output:
                on_output(f"Hata: {err}")
            return False, err
        except subprocess.TimeoutExpired:
            return False, "Kurulum zaman aşımına uğradı (5dk)"
        except FileNotFoundError:
            return False, f"Komut bulunamadı: {cmd[0]}"
        except OSError as e:
            return False, str(e)

    def install_instructions(self) -> str:
        """Platforma özgü manuel kurulum komutunu döndürür."""
        system = platform.system()
        if system == "Windows":
            return "winget install -e --id Cloudflare.Warp"
        if system == "Darwin":
            return "brew install --cask cloudflare-warp"
        return "https://developers.cloudflare.com/warp-client/get-started/linux/"
