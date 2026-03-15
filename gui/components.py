"""
Yeniden kullanılabilir GUI bileşenleri.
"""
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from core.constants import COLOR_SUCCESS, COLOR_ERROR, COLOR_LOG_INFO, COLOR_WARNING, LOG_MAX_LINES


class StatusIndicator(ctk.CTkFrame):
    """
    Renkli bir durum noktası ve metin etiketinden oluşan bileşen.
    Yeşil = bağlı, Kırmızı = bağlı değil, Gri = nötr/bilinmiyor.
    """

    def __init__(self, master, title: str, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.configure(corner_radius=12, fg_color=("gray90", "gray17"))

        self._title_label = ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=13, weight="bold")
        )
        self._title_label.pack(padx=15, pady=(12, 4))

        self._indicator_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._indicator_frame.pack(padx=15, pady=(0, 12))

        # Canvas arka plan rengini parent frame ile eşleştir
        bg = self._indicator_frame._apply_appearance_mode(("gray90", "gray17"))
        self._canvas = tk.Canvas(
            self._indicator_frame, width=14, height=14,
            highlightthickness=0, bg=bg
        )
        self._canvas.pack(side="left", padx=(0, 8))
        self._dot = self._canvas.create_oval(2, 2, 12, 12, fill="gray50", outline="")

        self._status_label = ctk.CTkLabel(
            self._indicator_frame, text="Bilinmiyor", font=ctk.CTkFont(size=12)
        )
        self._status_label.pack(side="left")

    def set_status(self, connected: bool, text: str = None) -> None:
        """Bağlı (yeşil) veya bağlı değil (kırmızı) durumunu gösterir."""
        color = COLOR_SUCCESS if connected else COLOR_ERROR
        default_text = "Bağlı" if connected else "Bağlı Değil"
        self._canvas.itemconfig(self._dot, fill=color)
        self._status_label.configure(text=text or default_text)

    def set_neutral(self, text: str = "Bilinmiyor") -> None:
        """Gri nötr durumu gösterir."""
        self._canvas.itemconfig(self._dot, fill="gray50")
        self._status_label.configure(text=text)


class LogPanel(ctk.CTkFrame):
    """
    Zaman damgalı ve renklendirilmiş mesajları gösteren kaydırılabilir log paneli.

    Desteklenen seviyeler: success, error, info, attempt.
    """

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)

        ctk.CTkLabel(
            self, text="Kayıtlar", font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=12, pady=(8, 4))

        self._textbox = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled", wrap="word"
        )
        self._textbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._textbox.tag_config("success", foreground=COLOR_SUCCESS)
        self._textbox.tag_config("error", foreground=COLOR_ERROR)
        self._textbox.tag_config("info", foreground=COLOR_LOG_INFO)
        self._textbox.tag_config("attempt", foreground=COLOR_WARNING)

    def append(self, message: str, level: str = "info") -> None:
        """Log paneline zaman damgalı mesaj ekler; satır sınırını korur."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        self._textbox.configure(state="normal")
        self._textbox.insert("end", line, level)
        self._textbox.configure(state="disabled")
        self._textbox.see("end")

        line_count = int(self._textbox.index("end-1c").split(".")[0])
        if line_count > LOG_MAX_LINES:
            self._textbox.configure(state="normal")
            self._textbox.delete("1.0", f"{line_count - LOG_MAX_LINES}.0")
            self._textbox.configure(state="disabled")

    def clear(self) -> None:
        """Tüm log içeriğini temizler."""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")
