import tkinter as tk
import customtkinter as ctk


class StatusIndicator(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(corner_radius=12, fg_color=("gray90", "gray17"))

        self._title_label = ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=13, weight="bold")
        )
        self._title_label.pack(padx=15, pady=(12, 4))

        self._indicator_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._indicator_frame.pack(padx=15, pady=(0, 12))

        self._canvas = tk.Canvas(
            self._indicator_frame, width=14, height=14,
            highlightthickness=0, bg=self._indicator_frame._apply_appearance_mode(
                ("gray90", "gray17")
            )
        )
        self._canvas.pack(side="left", padx=(0, 8))
        self._dot = self._canvas.create_oval(2, 2, 12, 12, fill="gray50", outline="")

        self._status_label = ctk.CTkLabel(
            self._indicator_frame, text="Bilinmiyor", font=ctk.CTkFont(size=12)
        )
        self._status_label.pack(side="left")

    def set_status(self, connected, text=None):
        color = "#2ecc71" if connected else "#e74c3c"
        default_text = "Bağlı" if connected else "Bağlı Değil"
        self._canvas.itemconfig(self._dot, fill=color)
        self._status_label.configure(text=text or default_text)

    def set_neutral(self, text="Bilinmiyor"):
        self._canvas.itemconfig(self._dot, fill="gray50")
        self._status_label.configure(text=text)


class LogPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._label = ctk.CTkLabel(
            self, text="Kayıtlar", font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self._label.pack(fill="x", padx=12, pady=(8, 4))

        self._textbox = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled", wrap="word"
        )
        self._textbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._textbox.tag_config("success", foreground="#2ecc71")
        self._textbox.tag_config("error", foreground="#e74c3c")
        self._textbox.tag_config("info", foreground="#95a5a6")
        self._textbox.tag_config("attempt", foreground="#f39c12")

    def append(self, message, level="info"):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        self._textbox.configure(state="normal")
        self._textbox.insert("end", line, level)
        self._textbox.configure(state="disabled")
        self._textbox.see("end")

        # Keep last 500 lines
        line_count = int(self._textbox.index("end-1c").split(".")[0])
        if line_count > 500:
            self._textbox.configure(state="normal")
            self._textbox.delete("1.0", f"{line_count - 500}.0")
            self._textbox.configure(state="disabled")

    def clear(self):
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")
