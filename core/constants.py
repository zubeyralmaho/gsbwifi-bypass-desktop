"""
Uygulama genelinde kullanılan sabitler ve enum'lar.
Magic değerlerin merkezi yönetimi için bu modülü kullanın.
"""
from enum import Enum


# ---------------------------------------------------------------------------
# Ağ sabitleri
# ---------------------------------------------------------------------------
LOGIN_URL = "https://wifi.gsb.gov.tr/j_spring_security_check"
LOGIN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/x-www-form-urlencoded",
}
DEFAULT_LOGIN_INTERVAL = 0.3   # saniye
LOGIN_REQUEST_TIMEOUT = 2      # saniye
INTERNET_CHECK_TIMEOUT = 3     # saniye

# ---------------------------------------------------------------------------
# WARP sabitleri
# ---------------------------------------------------------------------------
WARP_CONNECT_TIMEOUT = 10      # saniye
WARP_INSTALL_TIMEOUT = 300     # saniye (5 dakika)


class WarpStatus(str, Enum):
    """Cloudflare WARP bağlantı durumu."""
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    NOT_INSTALLED = "Not Installed"
    UNKNOWN = "Unknown"


# ---------------------------------------------------------------------------
# GUI sabitleri
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 850
WINDOW_HEIGHT = 580
MIN_WINDOW_WIDTH = 750
MIN_WINDOW_HEIGHT = 500

SIDEBAR_WIDTH = 170

LOG_MAX_LINES = 500

# Renk paleti
COLOR_SUCCESS = "#2ecc71"
COLOR_SUCCESS_HOVER = "#27ae60"
COLOR_ERROR = "#e74c3c"
COLOR_ERROR_HOVER = "#c0392b"
COLOR_INFO = "#3498db"
COLOR_INFO_HOVER = "#2980b9"
COLOR_WARNING = "#f39c12"
COLOR_LOG_INFO = "#95a5a6"
