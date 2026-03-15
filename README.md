# GSBWIFI Auto-Auth & Bypass

GSBWIFI ağlarında yaşanan "captive portal" erişim sorunlarına ve DPI (Deep Packet Inspection) tabanlı hız kısıtlamalarına (QoS) çözüm sağlayan cross-platform masaüstü uygulaması.

## Repo

- **GitHub (Public):** https://github.com/zubeyralmaho/gsbwifi-bypass-desktop

## Ekran Goruntusu

Asagidaki dosyayi eklediginizde README otomatik olarak onizleme gosterecektir:

`assets/app-preview.png`

![GSBWIFI Desktop UI](assets/app-preview.png)

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

## Hizli Baslangic

```bash
git clone https://github.com/zubeyralmaho/gsbwifi-bypass-desktop.git
cd gsbwifi-bypass
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
cp config.example.ini config.ini
python app.py
```

Windows icin aktivasyon komutu:

```powershell
.venv\Scripts\activate
```

## Kurulum

1. Repoyu klonlayın:
   ```bash
   git clone https://github.com/zubeyralmaho/gsbwifi-bypass-desktop.git
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

## İndirme (Hazır Paketler)

En son sürümü [GitHub Releases](https://github.com/zubeyralmaho/gsbwifi-bypass-desktop/releases/latest) sayfasından indirin:

| Platform | Dosya | Açıklama |
|----------|-------|----------|
| Windows  | `GSBWiFi-windows.zip` | `.exe` — Python gerekmez |
| macOS    | `GSBWiFi-macos.dmg`   | `.app` bundle — sürükle & bırak |
| Linux    | `GSBWiFi-linux.tar.gz`| Tek binary — `chmod +x` ile çalıştır |

### Linux kurulumu

```bash
tar -xzf GSBWiFi-linux.tar.gz
chmod +x GSBWiFi
./GSBWiFi
```

---

## Standalone Build (Geliştiriciler için)

### Gereksinimler

```bash
pip install -r requirements.txt
pip install -r build-requirements.txt
```

### İkon üretimi

```bash
python packaging/create_icons.py
```

### Paket oluşturma

```bash
# Tüm platformlar
make build

# macOS — .dmg dosyası
make dmg

# Linux — tar.gz paketi
make package-linux

# Temizlik
make clean
```

Veya doğrudan PyInstaller ile:

```bash
pyinstaller GSBWiFi.spec
```

### Otomatik CI/CD

`v*` etiketiyle push yapıldığında GitHub Actions otomatik olarak 3 platform için
paket oluşturur ve GitHub Release'e yükler:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Geliştiriciler
- Zübeyr Almaho — [GitHub](https://github.com/zubeyralmaho)
- Berkay Fehmi Tekin — [GitHub](https://github.com/berkayft)
