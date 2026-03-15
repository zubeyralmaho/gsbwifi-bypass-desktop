"""
Dashboard ekranı — durum göstergeleri, aksiyon butonları, istatistik ve log paneli.
"""
import customtkinter as ctk

from gui.components import StatusIndicator, LogPanel
from core.constants import (
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_ERROR,
    COLOR_ERROR_HOVER,
    COLOR_INFO,
    COLOR_INFO_HOVER,
    WarpStatus,
)


class DashboardFrame(ctk.CTkFrame):
    """GSBWIFI ve WARP bağlantı durumunu gösteren ve kontrol eden frame."""

    def __init__(self, master, app, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Log paneli row 3'te

        # Row 0: Durum kartları
        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        status_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.wifi_status = StatusIndicator(status_row, title="GSBWIFI")
        self.wifi_status.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.warp_status_indicator = StatusIndicator(status_row, title="WARP")
        self.warp_status_indicator.grid(row=0, column=1, sticky="ew", padx=6)

        self.monitor_status = StatusIndicator(status_row, title="Otomatik Bağlanma")
        self.monitor_status.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        # Row 1: Aksiyon butonları
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        self.btn_connect = ctk.CTkButton(
            btn_row, text="Ağa Bağlan", width=130,
            command=self._on_connect,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER
        )
        self.btn_connect.pack(side="left", padx=(0, 8))

        self.btn_warp_connect = ctk.CTkButton(
            btn_row, text="WARP Bağla", width=130,
            command=self._on_warp_connect,
            fg_color=COLOR_INFO, hover_color=COLOR_INFO_HOVER
        )
        self.btn_warp_connect.pack(side="left", padx=(0, 8))

        self.btn_warp_disconnect = ctk.CTkButton(
            btn_row, text="WARP Kes", width=110,
            command=self._on_warp_disconnect,
            fg_color=COLOR_ERROR, hover_color=COLOR_ERROR_HOVER
        )
        self.btn_warp_disconnect.pack(side="left", padx=(0, 8))

        self.btn_auto_reconnect = ctk.CTkButton(
            btn_row, text="Otomatik Bağlanma: Kapalı", width=180,
            command=self._toggle_auto_reconnect,
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40")
        )
        self.btn_auto_reconnect.pack(side="left")

        # Row 2: İstatistik kartı
        stats_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "gray14"))
        stats_card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        stats_card.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(
            stats_card, text="İstatistik",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray50"
        ).grid(row=0, column=0, padx=(14, 4), pady=8, sticky="w")

        self._lbl_total = ctk.CTkLabel(
            stats_card, text="Toplam: —",
            font=ctk.CTkFont(size=11)
        )
        self._lbl_total.grid(row=0, column=1, padx=4, pady=8)

        self._lbl_success = ctk.CTkLabel(
            stats_card, text="Başarılı: —",
            font=ctk.CTkFont(size=11)
        )
        self._lbl_success.grid(row=0, column=2, padx=4, pady=8)

        self._lbl_avg = ctk.CTkLabel(
            stats_card, text="Ort. Süre: —",
            font=ctk.CTkFont(size=11)
        )
        self._lbl_avg.grid(row=0, column=3, padx=4, pady=8)

        self.btn_clear_stats = ctk.CTkButton(
            stats_card, text="Temizle", width=70,
            command=self._clear_stats,
            fg_color=("gray75", "gray25"), hover_color=("gray65", "gray35"),
            font=ctk.CTkFont(size=11)
        )
        self.btn_clear_stats.grid(row=0, column=4, padx=(4, 14), pady=6)

        # Row 3: Log paneli
        self.log_panel = LogPanel(self)
        self.log_panel.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Log callback kaydı
        self.app.register_log_callback(self._on_log)

        # Monitor callback'leri
        self.app.monitor.on_status_change = lambda msg: self.app.after(
            0, self._monitor_status_changed, msg
        )
        self.app.monitor.on_reconnect_attempt = lambda msg: self.app.after(
            0, self._monitor_attempt, msg
        )

    # ------------------------------------------------------------------
    # Durum güncelleme
    # ------------------------------------------------------------------

    def refresh_status(self) -> None:
        """Tüm durum göstergelerini ve istatistik kartını günceller."""
        has_internet = False
        try:
            has_internet = self.app.auth_service.check_internet()
        except Exception:
            pass
        self.wifi_status.set_status(has_internet, "Bağlı" if has_internet else "Bağlı Değil")

        warp = self.app.warp_service.get_status()
        if warp == WarpStatus.CONNECTED:
            self.warp_status_indicator.set_status(True, "Aktif")
        elif warp == WarpStatus.DISCONNECTED:
            self.warp_status_indicator.set_status(False, "Pasif")
        elif warp == WarpStatus.NOT_INSTALLED:
            self.warp_status_indicator.set_neutral("Kurulu Değil")
        else:
            self.warp_status_indicator.set_neutral("Bilinmiyor")

        if self.app.monitor.is_running:
            self.monitor_status.set_status(True, "Aktif")
            self.btn_auto_reconnect.configure(
                text="Otomatik Bağlanma: Açık",
                fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER
            )
        else:
            self.monitor_status.set_status(False, "Kapalı")
            self.btn_auto_reconnect.configure(
                text="Otomatik Bağlanma: Kapalı",
                fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40")
            )

        self._refresh_stats()

    def _refresh_stats(self) -> None:
        """İstatistik kartını son verilerle günceller."""
        stats = self.app.history.get_stats()
        total = stats["total"]
        if total == 0:
            self._lbl_total.configure(text="Toplam: 0")
            self._lbl_success.configure(text="Başarılı: —")
            self._lbl_avg.configure(text="Ort. Süre: —")
            return

        self._lbl_total.configure(text=f"Toplam: {total}")
        self._lbl_success.configure(
            text=f"Başarılı: {stats['success']} (%{stats['rate']})"
        )
        avg = stats["avg_duration"]
        self._lbl_avg.configure(text=f"Ort. Süre: {avg}sn")

    def _clear_stats(self) -> None:
        self.app.history.clear()
        self._refresh_stats()
        self.log_panel.append("Bağlantı istatistikleri temizlendi.", "info")

    # ------------------------------------------------------------------
    # Aksiyon handler'ları
    # ------------------------------------------------------------------

    def _on_connect(self) -> None:
        tc = self.app.current_tc
        sifre = self.app.current_sifre
        if not tc or not sifre:
            self.log_panel.append("Önce giriş yapmalısınız!", "error")
            return

        self.btn_connect.configure(state="disabled")
        self.log_panel.append("GSBWIFI'ye bağlanılıyor...", "info")

        self.app.run_in_thread(
            self.app.auth_service.login,
            tc,
            sifre,
            on_attempt=lambda n, msg: self.app.after(
                0, self.log_panel.append, f"Deneme {n}: {msg}", "attempt"
            ),
            on_success=lambda n: self.app.after(0, self._connect_success, n),
            interval=self.app.settings.get("login_interval"),
        )

    def _connect_success(self, n: int) -> None:
        self.log_panel.append(f"GSBWIFI'ye {n}. denemede bağlanıldı!", "success")
        self.btn_connect.configure(state="normal")
        self.refresh_status()

    def _on_warp_connect(self) -> None:
        if not self.app.warp_service.is_installed():
            if not self.app.auth_service.check_internet():
                self.log_panel.append(
                    "WARP kurulumu için internet gerekli. Önce ağa bağlanın!", "error"
                )
                return
            self.log_panel.append("WARP kurulu değil, otomatik kurulum başlatılıyor...", "info")
            self.btn_warp_connect.configure(state="disabled", text="Kuruluyor...")
            self.app.run_in_thread(self._install_and_connect_warp)
        else:
            self.log_panel.append("WARP bağlantısı başlatılıyor...", "info")
            success, msg = self.app.warp_service.connect()
            self.log_panel.append(msg, "success" if success else "error")
            self.refresh_status()

    def _install_and_connect_warp(self) -> None:
        def on_output(msg: str) -> None:
            self.app.after(0, self.log_panel.append, msg, "info")

        success, msg = self.app.warp_service.auto_install(on_output=on_output)
        if success:
            self.app.after(0, self.log_panel.append, "WARP kurulumu tamamlandı!", "success")
            self.app.after(0, self.log_panel.append, "WARP bağlantısı başlatılıyor...", "info")
            conn_success, conn_msg = self.app.warp_service.connect()
            self.app.after(
                0, self.log_panel.append, conn_msg, "success" if conn_success else "error"
            )
        else:
            self.app.after(0, self.log_panel.append, f"WARP kurulumu başarısız: {msg}", "error")

        self.app.after(0, self._warp_install_done)

    def _warp_install_done(self) -> None:
        self.btn_warp_connect.configure(state="normal", text="WARP Bağla")
        self.refresh_status()

    def _on_warp_disconnect(self) -> None:
        success, msg = self.app.warp_service.disconnect()
        self.log_panel.append(msg, "success" if success else "error")
        self.refresh_status()

    def _toggle_auto_reconnect(self) -> None:
        if self.app.monitor.is_running:
            self.app.monitor.stop()
            self.log_panel.append("Otomatik bağlanma durduruldu.", "info")
        else:
            tc = self.app.current_tc
            sifre = self.app.current_sifre
            if not tc or not sifre:
                self.log_panel.append("Önce giriş yapmalısınız!", "error")
                return
            interval = self.app.settings.get("reconnect_interval")
            self.app.monitor.start(tc, sifre, interval=interval)
            self.log_panel.append(f"Otomatik bağlanma aktif ({interval}sn aralıkla).", "success")
        self.refresh_status()

    # ------------------------------------------------------------------
    # Monitor / log callback'leri
    # ------------------------------------------------------------------

    def _monitor_status_changed(self, msg: str) -> None:
        self.log_panel.append(msg, "info")
        self.refresh_status()

    def _monitor_attempt(self, msg: str) -> None:
        self.log_panel.append(msg, "attempt")

    def _on_log(self, level: str, message: str) -> None:
        self.log_panel.append(message, level)
