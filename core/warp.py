import os
import platform
import shutil
import subprocess
import glob as globmod


# macOS'ta warp-cli bilinen konumlar
_MACOS_WARP_PATHS = [
    "/usr/local/bin/warp-cli",
    "/Applications/Cloudflare WARP.app/Contents/Resources/warp-cli",
]

# Linux'ta bilinen konum
_LINUX_WARP_PATHS = [
    "/usr/bin/warp-cli",
    "/usr/local/bin/warp-cli",
]


class WarpService:
    def __init__(self):
        self._warp_cli_path = self._find_warp_cli()

    def _find_warp_cli(self):
        # Önce PATH'te ara
        found = shutil.which("warp-cli")
        if found:
            return found

        system = platform.system()
        search_paths = []
        if system == "Darwin":
            search_paths = _MACOS_WARP_PATHS
        elif system == "Linux":
            search_paths = _LINUX_WARP_PATHS

        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def is_installed(self):
        self._warp_cli_path = self._find_warp_cli()
        return self._warp_cli_path is not None

    def get_status(self):
        if not self.is_installed():
            return "Not Installed"
        try:
            result = subprocess.run(
                [self._warp_cli_path, "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "Connected" in result.stdout:
                return "Connected"
            return "Disconnected"
        except Exception:
            return "Unknown"

    def connect(self):
        if not self.is_installed():
            return False, "WARP kurulu değil"
        try:
            result = subprocess.run(
                [self._warp_cli_path, "connect"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, "WARP bağlantısı başlatıldı"
            return False, result.stderr.strip() or "Bağlantı başarısız"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if not self.is_installed():
            return False, "WARP kurulu değil"
        try:
            result = subprocess.run(
                [self._warp_cli_path, "disconnect"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, "WARP bağlantısı kesildi"
            return False, result.stderr.strip() or "Bağlantı kesilemedi"
        except Exception as e:
            return False, str(e)

    def auto_install(self, on_output=None):
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
                return success, msg if not success else "WARP başarıyla kuruldu"

            elif system == "Darwin":
                return self._install_macos(on_output)

            else:
                return self._install_linux(on_output)

        except Exception as e:
            return False, f"Kurulum hatası: {e}"

    def _install_macos(self, on_output=None):
        # Adım 1: brew ile .pkg dosyasını indir
        if shutil.which("brew"):
            success, msg = self._run_install(
                ["brew", "install", "--cask", "cloudflare-warp"],
                on_output,
            )
            if not success and "already installed" not in msg.lower():
                return False, msg
        else:
            return False, "Homebrew bulunamadı. Lütfen önce Homebrew kurun: https://brew.sh"

        # Adım 2: pkg dosyasını bul ve installer ile kur
        pkg_pattern = "/opt/homebrew/Caskroom/cloudflare-warp/*/Cloudflare_WARP_*.pkg"
        # Intel Mac'ler için de kontrol et
        pkg_pattern_intel = "/usr/local/Caskroom/cloudflare-warp/*/Cloudflare_WARP_*.pkg"

        pkg_files = globmod.glob(pkg_pattern) + globmod.glob(pkg_pattern_intel)
        if not pkg_files:
            return False, "WARP .pkg dosyası bulunamadı. brew indirimi başarısız olmuş olabilir."

        pkg_path = sorted(pkg_files)[-1]  # En son versiyonu al

        if on_output:
            on_output(f"WARP paketi kuruluyor: {os.path.basename(pkg_path)}")

        # installer komutu sudo gerektirir — osascript ile macOS'ta yetki iste
        success, msg = self._run_install(
            ["osascript", "-e",
             f'do shell script "installer -pkg \'{pkg_path}\' -target /" with administrator privileges'],
            on_output,
        )
        if success:
            self._warp_cli_path = self._find_warp_cli()
            return True, "WARP başarıyla kuruldu"
        return False, msg

    def _install_linux(self, on_output=None):
        if shutil.which("apt-get"):
            cmds = [
                ["sudo", "mkdir", "-p", "--mode=0755", "/usr/share/keyrings"],
                ["bash", "-c",
                 "curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg "
                 "| sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg"],
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

    def _run_install(self, cmd, on_output=None):
        try:
            if on_output:
                on_output(f"Çalıştırılıyor: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
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
        except Exception as e:
            return False, str(e)

    def install_instructions(self):
        system = platform.system()
        if system == "Windows":
            return "winget install -e --id Cloudflare.Warp"
        elif system == "Darwin":
            return "brew install --cask cloudflare-warp"
        else:
            return "https://developers.cloudflare.com/warp-client/get-started/linux/"
