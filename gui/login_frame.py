"""
Giriş / kimlik doğrulama ekranı.
"""
import customtkinter as ctk

from core.constants import (
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_INFO_HOVER,
    COLOR_WARNING,
)


class LoginFrame(ctk.CTkFrame):
    """GSBWIFI giriş formu ve ilerleme göstergesini içeren frame."""

    def __init__(self, master, app, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self, corner_radius=16, fg_color=("gray92", "gray14"))
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card, text="GSBWIFI Giriş",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(padx=40, pady=(30, 5))

        ctk.CTkLabel(
            card, text="Ağa bağlanmak için bilgilerinizi girin",
            font=ctk.CTkFont(size=12), text_color="gray50"
        ).pack(padx=40, pady=(0, 20))

        ctk.CTkLabel(
            card,
            text=(
                "Bu uygulama:\n"
                "• Basit ISS kısıtlamalarını aşmaya yardımcı olur\n"
                "• Halka açık ağlarda güvenliği artırır\n"
                "• DNS yanıtlarını hızlandırarak sayfa açılışını iyileştirir"
            ),
            justify="left",
            anchor="w",
            wraplength=340,
            font=ctk.CTkFont(size=12),
            text_color=("gray25", "gray75")
        ).pack(fill="x", padx=40, pady=(0, 16))

        ctk.CTkLabel(card, text="TC Kimlik No", anchor="w").pack(fill="x", padx=40)
        self.tc_entry = ctk.CTkEntry(
            card, placeholder_text="11 haneli TC kimlik numarası", width=280
        )
        self.tc_entry.pack(padx=40, pady=(4, 12))

        ctk.CTkLabel(card, text="Şifre", anchor="w").pack(fill="x", padx=40)
        self.pw_entry = ctk.CTkEntry(
            card, placeholder_text="Şifreniz", show="*", width=280
        )
        self.pw_entry.pack(padx=40, pady=(4, 12))

        self.remember_var = ctk.BooleanVar(value=self.app.settings.get("remember_credentials"))
        ctk.CTkCheckBox(
            card, text="Bilgilerimi Hatırla", variable=self.remember_var,
            font=ctk.CTkFont(size=12)
        ).pack(padx=40, pady=(0, 16))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(padx=40, pady=(0, 10))

        self.btn_login = ctk.CTkButton(
            btn_frame, text="Bağlan", width=130,
            command=self._on_login,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER
        )
        self.btn_login.pack(side="left", padx=(0, 8))

        self.btn_login_warp = ctk.CTkButton(
            btn_frame, text="Bağlan + WARP", width=140,
            command=self._on_login_warp,
            fg_color=COLOR_INFO, hover_color=COLOR_INFO_HOVER
        )
        self.btn_login_warp.pack(side="left")

        self.status_label = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=12), text_color=COLOR_WARNING
        )
        self.status_label.pack(padx=40, pady=(0, 8))

        self.progress = ctk.CTkProgressBar(card, width=280, mode="indeterminate")
        self.progress.pack(padx=40, pady=(0, 25))
        self.progress.set(0)
        self._progress_active = False
        self._with_warp = False

        # Kayıtlı kimlik bilgilerini yükle
        if self.app.settings.get("remember_credentials"):
            saved_tc = self.app.settings.get("saved_tc")
            if saved_tc:
                self.tc_entry.insert(0, saved_tc)
                saved_pw = self.app.settings.load_password(saved_tc)
                if saved_pw:
                    self.pw_entry.insert(0, saved_pw)

    # ------------------------------------------------------------------
    # Giriş akışı
    # ------------------------------------------------------------------

    def _validate(self):
        """TC/şifre girişini doğrular; hata varsa None döner."""
        tc = self.tc_entry.get().strip()
        sifre = self.pw_entry.get().strip()
        if not tc or not sifre:
            self.status_label.configure(
                text="TC ve Şifre alanları boş bırakılamaz!", text_color=COLOR_ERROR
            )
            return None, None
        if not tc.isdigit() or len(tc) != 11:
            self.status_label.configure(
                text="TC Kimlik 11 haneli sayı olmalıdır!", text_color=COLOR_ERROR
            )
            return None, None
        return tc, sifre

    def _on_login(self) -> None:
        self._with_warp = False
        self._start_login()

    def _on_login_warp(self) -> None:
        self._with_warp = True
        self._start_login()

    def _start_login(self) -> None:
        tc, sifre = self._validate()
        if tc is None:
            return

        if self.remember_var.get():
            self.app.settings.set("remember_credentials", True)
            self.app.settings.set("saved_tc", tc)
            self.app.settings.save_credentials(tc, sifre)
        else:
            self.app.settings.set("remember_credentials", False)
            self.app.settings.clear_credentials()

        self.btn_login.configure(state="disabled")
        self.btn_login_warp.configure(state="disabled")
        if not self._progress_active:
            self.progress.start()
            self._progress_active = True
        self.status_label.configure(text="Bağlanılıyor...", text_color=COLOR_WARNING)

        self.app.current_tc = tc
        self.app.current_sifre = sifre

        self.app.run_in_thread(
            self.app.auth_service.login,
            tc,
            sifre,
            on_attempt=self._on_attempt,
            on_success=self._on_success,
            interval=self.app.settings.get("login_interval"),
        )

    # ------------------------------------------------------------------
    # Callback'ler (arka plan thread'inden çağrılır)
    # ------------------------------------------------------------------

    def _on_attempt(self, n: int, msg: str) -> None:
        self.app.after(0, self._update_attempt, n, msg)

    def _on_success(self, n: int) -> None:
        self.app.after(0, self._handle_success, n)

    def _update_attempt(self, n: int, msg: str) -> None:
        self.status_label.configure(text=f"Deneme {n}: {msg}", text_color=COLOR_WARNING)
        self.app.log("attempt", f"Deneme {n}: {msg}")

    def _handle_success(self, n: int) -> None:
        if self._progress_active:
            self.progress.stop()
            self.progress.set(1)
            self._progress_active = False
        self.status_label.configure(
            text=f"{n}. denemede bağlantı başarılı!", text_color=COLOR_SUCCESS
        )
        self.btn_login.configure(state="normal")
        self.btn_login_warp.configure(state="normal")
        self.app.log("success", f"GSBWIFI'ye {n}. denemede bağlanıldı!")
        self.app.notifier.send("GSBWIFI Bypass", f"Bağlandı! ({n}. denemede)")

        if self._with_warp:
            if not self.app.warp_service.is_installed():
                self.app.log("info", "WARP kurulu değil, otomatik kurulum başlatılıyor...")
                self.status_label.configure(text="WARP kuruluyor...", text_color=COLOR_WARNING)
                self.app.run_in_thread(self._install_and_connect_warp)
                return
            self.app.log("info", "WARP bağlantısı başlatılıyor...")
            success, msg = self.app.warp_service.connect()
            self.app.log("success" if success else "error", msg)

        self.app.show_frame("dashboard")

    def _install_and_connect_warp(self) -> None:
        def on_output(msg: str) -> None:
            self.app.after(0, self.app.log, "info", msg)

        success, msg = self.app.warp_service.auto_install(on_output=on_output)
        if success:
            self.app.after(0, self.app.log, "success", "WARP kurulumu tamamlandı!")
            self.app.after(0, self.app.log, "info", "WARP bağlantısı başlatılıyor...")
            conn_success, conn_msg = self.app.warp_service.connect()
            self.app.after(0, self.app.log, "success" if conn_success else "error", conn_msg)
        else:
            self.app.after(0, self.app.log, "error", f"WARP kurulumu başarısız: {msg}")

        self.app.after(0, self.app.show_frame, "dashboard")
