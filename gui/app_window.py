import customtkinter as ctk
from core.auth import AuthService
from core.warp import WarpService
from core.settings import Settings
from core.monitor import ReconnectMonitor
from gui.login_frame import LoginFrame


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GSBWIFI Bypass")
        self.geometry("850x580")
        self.minsize(750, 500)

        # Services
        self.auth_service = AuthService()
        self.warp_service = WarpService()
        self.settings = Settings()
        self.monitor = ReconnectMonitor(self.auth_service)

        # Current credentials (set after login)
        self.current_tc = ""
        self.current_sifre = ""

        # Log entries (shared across frames)
        self._log_callbacks = []

        # Apply appearance
        ctk.set_appearance_mode(self.settings.get("appearance_mode"))
        ctk.set_default_color_theme("green")

        # Layout: sidebar + content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=170, corner_radius=0, fg_color=("gray85", "gray10"))
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

        # Credits at bottom of sidebar
        credits = ctk.CTkLabel(
            self.sidebar,
            text="by Zübeyr Almaho\n& Berkay Fehmi Tekin",
            font=ctk.CTkFont(size=10),
            text_color="gray50"
        )
        credits.pack(side="bottom", padx=12, pady=15)

        # Content area
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Frames
        self.frames = {}
        self._create_frames()

        # Start on login
        self.show_frame("login")

        # Close handler
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_frames(self):
        self.frames["login"] = LoginFrame(self.content, app=self)
        self.frames["login"].grid(row=0, column=0, sticky="nsew")

        # Dashboard and settings are imported lazily to avoid circular imports
        from gui.dashboard_frame import DashboardFrame
        from gui.settings_frame import SettingsFrame

        self.frames["dashboard"] = DashboardFrame(self.content, app=self)
        self.frames["dashboard"].grid(row=0, column=0, sticky="nsew")

        self.frames["settings"] = SettingsFrame(self.content, app=self)
        self.frames["settings"].grid(row=0, column=0, sticky="nsew")

    def show_frame(self, name):
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()
            if name == "dashboard":
                self.frames["dashboard"].refresh_status()

    def log(self, level, message):
        for callback in self._log_callbacks:
            callback(level, message)

    def register_log_callback(self, callback):
        self._log_callbacks.append(callback)

    def _logout(self):
        self.auth_service.stop()
        self.monitor.stop()
        self.current_tc = ""
        self.current_sifre = ""
        self.show_frame("login")

    def _on_closing(self):
        self.auth_service.stop()
        self.monitor.stop()
        self.settings.save()
        self.destroy()
