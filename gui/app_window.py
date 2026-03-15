"""
Ana uygulama penceresi ve frame yöneticisi.
"""
import threading
from typing import Callable, List

import customtkinter as ctk

from core.auth import AuthService
from core.warp import WarpService
from core.settings import Settings
from core.monitor import ReconnectMonitor
from core.constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    SIDEBAR_WIDTH,
)
from gui.login_frame import LoginFrame


class AppWindow(ctk.CTk):
    """
    GSBWIFI Bypass ana penceresi.

    Sidebar navigasyonu, servis yaşam döngüsü ve frame'ler arası
    log callback yönetimini koordine eder.
    """

    def __init__(self) -> None:
        super().__init__()

        self.title("GSBWIFI Bypass")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Servisler
        self.auth_service = AuthService()
        self.warp_service = WarpService()
        self.settings = Settings()
        self.monitor = ReconnectMonitor(self.auth_service)

        # Giriş sonrası mevcut kimlik bilgileri
        self.current_tc: str = ""
        self.current_sifre: str = ""

        # Log callback'leri ve thread takibi
        self._log_callbacks: List[Callable] = []
        self._threads: List[threading.Thread] = []

        ctk.set_appearance_mode(self.settings.get("appearance_mode"))
        ctk.set_default_color_theme("green")

        # Yerleşim: sidebar + içerik alanı
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=("gray85", "gray10")
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        logo_label = ctk.CTkLabel(
            self.sidebar, text="GSBWIFI\nBypass",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        logo_label.pack(padx=20, pady=(25, 30))

        self.btn_dashboard = ctk.CTkButton(
            self.sidebar, text="Dashboard", command=lambda: self.show_frame("dashboard"),
            fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray25"), anchor="w"
        )
        self.btn_dashboard.pack(fill="x", padx=12, pady=(0, 4))

        self.btn_settings = ctk.CTkButton(
            self.sidebar, text="Ayarlar", command=lambda: self.show_frame("settings"),
            fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray25"), anchor="w"
        )
        self.btn_settings.pack(fill="x", padx=12, pady=(0, 4))

        self.btn_logout = ctk.CTkButton(
            self.sidebar, text="Çıkış Yap", command=self._logout,
            fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray25"), anchor="w"
        )
        self.btn_logout.pack(fill="x", padx=12, pady=(0, 4))

        credits = ctk.CTkLabel(
            self.sidebar,
            text="by Zübeyr Almaho\n& Berkay Fehmi Tekin",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        credits.pack(side="bottom", padx=12, pady=15)

        # İçerik alanı
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.frames: dict = {}
        self._create_frames()

        self.show_frame("login")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ------------------------------------------------------------------
    # Frame yönetimi
    # ------------------------------------------------------------------

    def _create_frames(self) -> None:
        from gui.dashboard_frame import DashboardFrame
        from gui.settings_frame import SettingsFrame

        self.frames["login"] = LoginFrame(self.content, app=self)
        self.frames["login"].grid(row=0, column=0, sticky="nsew")

        self.frames["dashboard"] = DashboardFrame(self.content, app=self)
        self.frames["dashboard"].grid(row=0, column=0, sticky="nsew")

        self.frames["settings"] = SettingsFrame(self.content, app=self)
        self.frames["settings"].grid(row=0, column=0, sticky="nsew")

    def show_frame(self, name: str) -> None:
        """Belirtilen frame'i öne getirir."""
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()
            if name == "dashboard":
                self.frames["dashboard"].refresh_status()

    # ------------------------------------------------------------------
    # Log sistemi
    # ------------------------------------------------------------------

    def log(self, level: str, message: str) -> None:
        """Kayıtlı tüm callback'lere log iletisi gönderir."""
        for callback in self._log_callbacks:
            callback(level, message)

    def register_log_callback(self, callback: Callable) -> None:
        """Log callback'i kaydeder."""
        self._log_callbacks.append(callback)

    # ------------------------------------------------------------------
    # Thread yönetimi
    # ------------------------------------------------------------------

    def run_in_thread(self, target: Callable, *args, **kwargs) -> threading.Thread:
        """
        Daemon thread oluşturur, başlatır ve referansını saklar.

        Args:
            target: Thread'de çalıştırılacak çağrılabilir.
            *args, **kwargs: target'a iletilecek argümanlar.

        Returns:
            Başlatılmış Thread nesnesi.
        """
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        self._threads.append(thread)
        thread.start()
        return thread

    # ------------------------------------------------------------------
    # Uygulama yaşam döngüsü
    # ------------------------------------------------------------------

    def _logout(self) -> None:
        """Servisleri durdurur ve login ekranına döner."""
        self.auth_service.stop()
        self.monitor.stop()
        self.current_tc = ""
        self.current_sifre = ""
        self.show_frame("login")

    def _on_closing(self) -> None:
        """Pencere kapatılırken servisleri temizler."""
        self.auth_service.stop()
        self.monitor.stop()
        self.settings.save()
        self.destroy()
