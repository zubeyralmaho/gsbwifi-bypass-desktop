"""
Bağlantı geçmişi ve istatistik yönetimi.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.constants import HISTORY_MAX_EVENTS


class ConnectionHistory:
    """
    Yeniden bağlanma olaylarını JSON dosyasında saklar ve istatistik üretir.

    Her olay:
        {
            "ts": "2026-03-15T14:32:45.123Z",  # ISO 8601 UTC
            "attempts": 3,                      # Deneme sayısı
            "duration": 8.2,                    # Saniye cinsinden süre
            "success": true,
            "error": null                       # Başarısızsa hata mesajı
        }
    """

    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "connection_history.json"
        self._events: list = []
        self._load()

    # ------------------------------------------------------------------
    # Yükleme / kaydetme
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._events = data
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Uyarı] Bağlantı geçmişi okunamadı: {e}", file=sys.stderr)

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._events, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Hata] Bağlantı geçmişi kaydedilemedi: {e}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Olay ekleme
    # ------------------------------------------------------------------

    def add_reconnect(
        self,
        attempts: int,
        duration: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Yeniden bağlanma olayını kaydeder.

        Args:
            attempts: Kaç denemede sonuca ulaşıldı.
            duration: Bağlantı kopmasından itibaren geçen saniye.
            success: Yeniden bağlanma başarılı mı?
            error: Başarısızsa hata açıklaması.
        """
        event = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "attempts": attempts,
            "duration": round(duration, 1),
            "success": success,
            "error": error,
        }
        self._events.append(event)

        # Maksimum olay sayısını aş
        if len(self._events) > HISTORY_MAX_EVENTS:
            self._events = self._events[-HISTORY_MAX_EVENTS:]

        self._save()

    # ------------------------------------------------------------------
    # Sorgulama
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """
        Özet istatistikleri döndürür.

        Returns:
            {
                "total": int,         # Toplam olay sayısı
                "success": int,       # Başarılı olay sayısı
                "rate": float,        # Başarı oranı (0-100)
                "avg_duration": float # Başarılı bağlanmaların ortalama süresi (sn)
            }
        """
        if not self._events:
            return {"total": 0, "success": 0, "rate": 0.0, "avg_duration": 0.0}

        total = len(self._events)
        successes = [e for e in self._events if e.get("success")]
        success_count = len(successes)
        rate = success_count / total * 100
        avg_duration = (
            sum(e["duration"] for e in successes) / success_count
            if successes else 0.0
        )
        return {
            "total": total,
            "success": success_count,
            "rate": round(rate, 1),
            "avg_duration": round(avg_duration, 1),
        }

    def get_recent(self, n: int = 20) -> list:
        """En son n olayı yeniden eskiye sıralı döndürür."""
        return list(reversed(self._events[-n:]))

    def clear(self) -> None:
        """Tüm geçmişi siler."""
        self._events = []
        self._save()
