import threading
import customtkinter as ctk
from gui.components import StatusIndicator, LogPanel


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Top: Status cards
        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        status_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.wifi_status = StatusIndicator(status_row, title="GSBWIFI")
        self.wifi_status.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.warp_status = StatusIndicator(status_row, title="WARP")
        self.warp_status.grid(row=0, column=1, sticky="ew", padx=6)

        self.monitor_status = StatusIndicator(status_row, title="Otomatik Bağlanma")
        self.monitor_status.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        # Middle: Action buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        self.btn_connect = ctk.CTkButton(
            btn_row, text="Ağa Bağlan", width=130,
            command=self._on_connect,
            fg_color="#2ecc71", hover_color="#27ae60"
        )
        self.btn_connect.pack(side="left", padx=(0, 8))

        self.btn_warp_connect = ctk.CTkButton(
            btn_row, text="WARP Bağla", width=130,
            command=self._on_warp_connect,
            fg_color="#3498db", hover_color="#2980b9"
        )
        self.btn_warp_connect.pack(side="left", padx=(0, 8))

        self.btn_warp_disconnect = ctk.CTkButton(
            btn_row, text="WARP Kes", width=110,
            command=self._on_warp_disconnect,
            fg_color="#e74c3c", hover_color="#c0392b"
        )
        self.btn_warp_disconnect.pack(side="left", padx=(0, 8))

        self.btn_auto_reconnect = ctk.CTkButton(
            btn_row, text="Otomatik Bağlanma: Kapalı", width=180,
            command=self._toggle_auto_reconnect,
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40")
        )
        self.btn_auto_reconnect.pack(side="left")

        # Bottom: Log panel
        self.log_panel = LogPanel(self)
        self.log_panel.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Register log callback
        self.app.register_log_callback(self._on_log)

        # Monitor callbacks
        self.app.monitor.on_status_change = lambda msg: self.app.after(0, self._monitor_status_changed, msg)
        self.app.monitor.on_reconnect_attempt = lambda msg: self.app.after(0, self._monitor_attempt, msg)

    def refresh_status(self):
        # WiFi status
        has_internet = False
        try:
            has_internet = self.app.auth_service.check_internet()
        except Exception:
            pass
        self.wifi_status.set_status(has_internet, "Bağlı" if has_internet else "Bağlı Değil")

        # WARP status
        warp_status = self.app.warp_service.get_status()
        if warp_status == "Connected":
            self.warp_status.set_status(True, "Aktif")
        elif warp_status == "Disconnected":
            self.warp_status.set_status(False, "Pasif")
        elif warp_status == "Not Installed":
            self.warp_status.set_neutral("Kurulu Değil")
        else:
            self.warp_status.set_neutral("Bilinmiyor")

        # Monitor status
        if self.app.monitor.is_running:
            self.monitor_status.set_status(True, "Aktif")
            self.btn_auto_reconnect.configure(
                text="Otomatik Bağlanma: Açık",
                fg_color="#2ecc71", hover_color="#27ae60"
            )
        else:
            self.monitor_status.set_status(False, "Kapalı")
            self.btn_auto_reconnect.configure(
                text="Otomatik Bağlanma: Kapalı",
                fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40")
            )

    def _on_connect(self):
        tc = self.app.current_tc
        sifre = self.app.current_sifre
        if not tc or not sifre:
            self.log_panel.append("Önce giriş yapmalısınız!", "error")
            return

        self.btn_connect.configure(state="disabled")
        self.log_panel.append("GSBWIFI'ye bağlanılıyor...", "info")

        thread = threading.Thread(
            target=self.app.auth_service.login,
            args=(tc, sifre),
            kwargs={
                "on_attempt": lambda n, msg: self.app.after(0, self.log_panel.append, f"Deneme {n}: {msg}", "attempt"),
                "on_success": lambda n: self.app.after(0, self._connect_success, n),
                "interval": self.app.settings.get("login_interval"),
            },
            daemon=True,
        )
        thread.start()

    def _connect_success(self, n):
        self.log_panel.append(f"GSBWIFI'ye {n}. denemede bağlanıldı!", "success")
        self.btn_connect.configure(state="normal")
        self.refresh_status()

    def _on_warp_connect(self):
        if not self.app.warp_service.is_installed():
            if not self.app.auth_service.check_internet():
                self.log_panel.append("WARP kurulumu için internet gerekli. Önce ağa bağlanın!", "error")
                return
            self.log_panel.append("WARP kurulu değil, otomatik kurulum başlatılıyor...", "info")
            self.btn_warp_connect.configure(state="disabled", text="Kuruluyor...")
            thread = threading.Thread(
                target=self._install_and_connect_warp, daemon=True
            )
            thread.start()
        else:
            self.log_panel.append("WARP bağlantısı başlatılıyor...", "info")
            success, msg = self.app.warp_service.connect()
            level = "success" if success else "error"
            self.log_panel.append(msg, level)
            self.refresh_status()

    def _install_and_connect_warp(self):
        def on_output(msg):
            self.app.after(0, self.log_panel.append, msg, "info")

        success, msg = self.app.warp_service.auto_install(on_output=on_output)
        if success:
            self.app.after(0, self.log_panel.append, "WARP kurulumu tamamlandı!", "success")
            self.app.after(0, self.log_panel.append, "WARP bağlantısı başlatılıyor...", "info")
            conn_success, conn_msg = self.app.warp_service.connect()
            level = "success" if conn_success else "error"
            self.app.after(0, self.log_panel.append, conn_msg, level)
        else:
            self.app.after(0, self.log_panel.append, f"WARP kurulumu başarısız: {msg}", "error")

        self.app.after(0, self._warp_install_done)

    def _warp_install_done(self):
        self.btn_warp_connect.configure(state="normal", text="WARP Bağla")
        self.refresh_status()

    def _on_warp_disconnect(self):
        success, msg = self.app.warp_service.disconnect()
        level = "success" if success else "error"
        self.log_panel.append(msg, level)
        self.refresh_status()

    def _toggle_auto_reconnect(self):
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

    def _monitor_status_changed(self, msg):
        self.log_panel.append(msg, "info")
        self.refresh_status()

    def _monitor_attempt(self, msg):
        self.log_panel.append(msg, "attempt")

    def _on_log(self, level, message):
        self.log_panel.append(message, level)
