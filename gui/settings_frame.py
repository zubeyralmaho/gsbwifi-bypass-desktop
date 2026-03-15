"""
Ayarlar ekranı — tema, yeniden bağlanma, kimlik bilgileri ve WARP yönetimi.
"""
import threading

import customtkinter as ctk

from core.constants import (
    COLOR_ERROR,
    COLOR_ERROR_HOVER,
    COLOR_INFO,
    COLOR_INFO_HOVER,
    WarpStatus,
)


class SettingsFrame(ctk.CTkFrame):
    """Uygulama tercihlerini düzenlemeye yarayan frame."""

    def __init__(self, master, app, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Ayarlar",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 16))

        # Genel ayarlar kartı
        card = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray92", "gray14"))
        card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)

        row = 0

        ctk.CTkLabel(card, text="Tema", font=ctk.CTkFont(size=13)).grid(
            row=row, column=0, sticky="w", padx=20, pady=(16, 8)
        )
        self.appearance_menu = ctk.CTkOptionMenu(
            card, values=["System", "Light", "Dark"],
            command=self._on_appearance_change, width=140
        )
        self.appearance_menu.set(self.app.settings.get("appearance_mode"))
        self.appearance_menu.grid(row=row, column=1, sticky="e", padx=20, pady=(16, 8))
        row += 1

        ctk.CTkLabel(
            card, text="Otomatik Yeniden Bağlanma", font=ctk.CTkFont(size=13)
        ).grid(row=row, column=0, sticky="w", padx=20, pady=8)
        self.auto_reconnect_var = ctk.BooleanVar(value=self.app.settings.get("auto_reconnect"))
        ctk.CTkSwitch(
            card, text="", variable=self.auto_reconnect_var,
            command=self._on_auto_reconnect_change
        ).grid(row=row, column=1, sticky="e", padx=20, pady=8)
        row += 1

        ctk.CTkLabel(
            card, text="Kontrol Aralığı (sn)", font=ctk.CTkFont(size=13)
        ).grid(row=row, column=0, sticky="w", padx=20, pady=8)
        interval_frame = ctk.CTkFrame(card, fg_color="transparent")
        interval_frame.grid(row=row, column=1, sticky="e", padx=20, pady=8)
        self.interval_label = ctk.CTkLabel(
            interval_frame,
            text=f"{self.app.settings.get('reconnect_interval')}s",
            font=ctk.CTkFont(size=12), width=35
        )
        self.interval_label.pack(side="right")
        self.interval_slider = ctk.CTkSlider(
            interval_frame, from_=5, to=60, number_of_steps=11, width=140,
            command=self._on_interval_change
        )
        self.interval_slider.set(self.app.settings.get("reconnect_interval"))
        self.interval_slider.pack(side="right", padx=(0, 8))
        row += 1

        ctk.CTkLabel(
            card, text="Giriş İstek Aralığı (sn)", font=ctk.CTkFont(size=13)
        ).grid(row=row, column=0, sticky="w", padx=20, pady=8)
        login_int_frame = ctk.CTkFrame(card, fg_color="transparent")
        login_int_frame.grid(row=row, column=1, sticky="e", padx=20, pady=8)
        self.login_interval_label = ctk.CTkLabel(
            login_int_frame,
            text=f"{self.app.settings.get('login_interval')}s",
            font=ctk.CTkFont(size=12), width=35
        )
        self.login_interval_label.pack(side="right")
        self.login_interval_slider = ctk.CTkSlider(
            login_int_frame, from_=0.1, to=2.0, number_of_steps=19, width=140,
            command=self._on_login_interval_change
        )
        self.login_interval_slider.set(self.app.settings.get("login_interval"))
        self.login_interval_slider.pack(side="right", padx=(0, 8))
        row += 1

        ctk.CTkLabel(
            card, text="Bilgileri Hatırla", font=ctk.CTkFont(size=13)
        ).grid(row=row, column=0, sticky="w", padx=20, pady=8)
        self.remember_var = ctk.BooleanVar(value=self.app.settings.get("remember_credentials"))
        ctk.CTkSwitch(
            card, text="", variable=self.remember_var,
            command=self._on_remember_change
        ).grid(row=row, column=1, sticky="e", padx=20, pady=8)
        row += 1

        ctk.CTkLabel(
            card, text="Bildirimler", font=ctk.CTkFont(size=13)
        ).grid(row=row, column=0, sticky="w", padx=20, pady=8)
        self.notifications_var = ctk.BooleanVar(
            value=self.app.settings.get("notifications_enabled")
        )
        ctk.CTkSwitch(
            card, text="", variable=self.notifications_var,
            command=self._on_notifications_change
        ).grid(row=row, column=1, sticky="e", padx=20, pady=8)
        row += 1

        self.btn_clear_creds = ctk.CTkButton(
            card, text="Kayıtlı Bilgileri Temizle", width=180,
            command=self._clear_credentials,
            fg_color=COLOR_ERROR, hover_color=COLOR_ERROR_HOVER
        )
        self.btn_clear_creds.grid(row=row, column=0, columnspan=2, padx=20, pady=(8, 16))

        # WARP kartı
        warp_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray92", "gray14"))
        warp_card.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        warp_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            warp_card, text="Cloudflare WARP",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        warp_status = self.app.warp_service.get_status()
        status_text = {
            WarpStatus.CONNECTED: "Bağlı",
            WarpStatus.DISCONNECTED: "Bağlı Değil",
            WarpStatus.NOT_INSTALLED: "Kurulu Değil",
        }.get(warp_status, "Bilinmiyor")

        ctk.CTkLabel(
            warp_card, text=f"Durum: {status_text}",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=1, sticky="e", padx=20, pady=(16, 8))

        btn_frame = ctk.CTkFrame(warp_card, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 16))

        self.btn_warp_install = ctk.CTkButton(
            btn_frame, text="Otomatik Kur", width=140,
            command=self._auto_install_warp,
            fg_color=COLOR_INFO, hover_color=COLOR_INFO_HOVER
        )
        self.btn_warp_install.pack(side="left", padx=(0, 8))

        install_cmd = self.app.warp_service.install_instructions()
        self.btn_copy_cmd = ctk.CTkButton(
            btn_frame, text="Komutu Kopyala", width=140,
            command=lambda: self._copy_to_clipboard(install_cmd),
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40")
        )
        self.btn_copy_cmd.pack(side="left")

        if self.app.warp_service.is_installed():
            self.btn_warp_install.configure(text="Kurulu", state="disabled")

    # ------------------------------------------------------------------
    # Ayar değişiklik handler'ları
    # ------------------------------------------------------------------

    def _on_appearance_change(self, value: str) -> None:
        ctk.set_appearance_mode(value)
        self.app.settings.set("appearance_mode", value)

    def _on_auto_reconnect_change(self) -> None:
        self.app.settings.set("auto_reconnect", self.auto_reconnect_var.get())

    def _on_interval_change(self, value: float) -> None:
        val = int(round(value))
        self.interval_label.configure(text=f"{val}s")
        self.app.settings.set("reconnect_interval", val)

    def _on_login_interval_change(self, value: float) -> None:
        val = round(value, 1)
        self.login_interval_label.configure(text=f"{val}s")
        self.app.settings.set("login_interval", val)

    def _on_remember_change(self) -> None:
        self.app.settings.set("remember_credentials", self.remember_var.get())

    def _on_notifications_change(self) -> None:
        self.app.settings.set("notifications_enabled", self.notifications_var.get())

    def _clear_credentials(self) -> None:
        self.app.settings.clear_credentials()
        self.remember_var.set(False)
        self.btn_clear_creds.configure(text="Temizlendi!", state="disabled")
        self.after(2000, lambda: self.btn_clear_creds.configure(
            text="Kayıtlı Bilgileri Temizle", state="normal"
        ))

    # ------------------------------------------------------------------
    # WARP kurulum
    # ------------------------------------------------------------------

    def _auto_install_warp(self) -> None:
        if not self.app.auth_service.check_internet():
            self.app.log("error", "WARP kurulumu için internet gerekli. Önce GSBWIFI'ye bağlanın!")
            return
        self.btn_warp_install.configure(text="Kuruluyor...", state="disabled")
        thread = threading.Thread(target=self._run_warp_install, daemon=True)
        thread.start()

    def _run_warp_install(self) -> None:
        def on_output(msg: str) -> None:
            self.app.after(0, self.app.log, "info", msg)

        success, msg = self.app.warp_service.auto_install(on_output=on_output)
        if success:
            self.app.after(0, self.app.log, "success", "WARP başarıyla kuruldu!")
            self.app.after(0, self.btn_warp_install.configure, text="Kurulu", state="disabled")
        else:
            self.app.after(0, self.app.log, "error", f"WARP kurulumu başarısız: {msg}")
            self.app.after(0, self.btn_warp_install.configure, text="Otomatik Kur", state="normal")

    def _copy_to_clipboard(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.btn_copy_cmd.configure(text="Kopyalandı!")
        self.after(2000, lambda: self.btn_copy_cmd.configure(text="Komutu Kopyala"))
