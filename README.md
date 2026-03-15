# GSBWIFI Auto-Auth & Bypass

GSBWIFI ağlarında yaşanan "captive portal" erişim sorunlarına ve DPI (Deep Packet Inspection) tabanlı hız kısıtlamalarına (QoS) çözüm sağlayan cross-platform masaüstü uygulaması.

## Bu Uygulama Ne Yapar?

- **Basit ISS kısıtlamalarını aşmaya yardımcı olur:** Ağ trafiğini Cloudflare WARP üzerinden tünelleyerek bazı temel trafik şekillendirme/engelleme kurallarının etkisini azaltır.
- **Halka açık ağlarda güvenliği artırır:** Kafe, kütüphane gibi ortak ağlarda trafiği tünelleyerek bağlantıyı daha güvenli hale getirir.
- **DNS yanıtlarını iyileştirir:** WARP'ın optimize DNS yönlendirmesiyle bazı sitelerde daha hızlı alan adı çözümlemesi ve daha seri açılış sağlayabilir.

## Özellikler

- **Hızlı Doğrulama (Auto-Auth):** `j_spring_security_check` endpoint'ine agresif POST istekleri atarak saniyeler içinde ağa yetkilendirme sağlar.
- **Hız Kısıtı Aşma (DPI Bypass):** Cloudflare WARP entegrasyonu ile trafik şekillendirme filtrelerini atlar.
- **Modern Arayüz:** CustomTkinter ile oluşturulmuş, koyu/açık tema destekli masaüstü uygulaması.
- **Gerçek Zamanlı Durum:** Bağlantı durumu göstergeleri ve detaylı log paneli.
- **Otomatik Yeniden Bağlanma:** Bağlantı koptuğunda otomatik olarak tekrar giriş yapan arka plan servisi.
- **Güvenli Kimlik Yönetimi:** Kimlik bilgileri isteğe bağlı olarak lokal olarak saklanır.
- **Cross-Platform:** Windows, macOS ve Linux desteği.

## Kurulum

1. Repoyu klonlayın:
   ```bash
   git clone https://github.com/zubeyralmaho/gsbwifi-bypass.git
   cd gsbwifi-bypass
   ```

2. Sanal ortam oluşturun ve bağımlılıkları yükleyin:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # veya: .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. Uygulamayı başlatın:
   ```bash
   python app.py
   ```

## Kullanım

1. **Giriş Ekranı:** TC Kimlik ve şifrenizi girin, "Bağlan" veya "Bağlan + WARP" butonuna tıklayın.
2. **Dashboard:** Bağlantı durumunu takip edin, WARP'ı yönetin, otomatik bağlanmayı aktif edin.
3. **Ayarlar:** Tema, bağlantı aralıkları ve kimlik bilgisi kaydetme tercihlerinizi yapılandırın.

## Cloudflare WARP Kurulumu

| Platform | Komut |
|----------|-------|
| Windows  | `winget install -e --id Cloudflare.Warp` |
| macOS    | `brew install cloudflare-warp` |
| Linux    | [Resmi Dokümantasyon](https://developers.cloudflare.com/warp-client/get-started/linux/) |

## Standalone Build (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name GSBWiFi app.py
```

## Geliştiriciler
- Zübeyr Almaho — [GitHub](https://github.com/zubeyralmaho)
- Berkay Fehmi Tekin — [GitHub](https://github.com/berkayft)
