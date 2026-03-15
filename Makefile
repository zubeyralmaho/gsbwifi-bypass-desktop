.PHONY: icons build dmg package-linux clean help

# Varsayılan hedef
help:
	@echo "Kullanılabilir hedefler:"
	@echo "  icons         — assets/ klasörüne ikonları üretir (Pillow gerekli)"
	@echo "  build         — PyInstaller ile mevcut platform için paket oluşturur"
	@echo "  dmg           — macOS .dmg dosyası oluşturur (sadece macOS)"
	@echo "  package-linux — Linux tar.gz paketi oluşturur"
	@echo "  clean         — build/dist ve üretilen dosyaları temizler"

icons:
	python packaging/create_icons.py

build: icons
	pyinstaller GSBWiFi.spec

dmg: build
	hdiutil create \
		-volname "GSBWIFI Bypass" \
		-srcfolder dist/GSBWiFi.app \
		-ov \
		-format UDZO \
		GSBWiFi-macos.dmg
	@echo "Oluşturuldu: GSBWiFi-macos.dmg"

package-linux: build
	mkdir -p release
	tar -czf release/GSBWiFi-linux.tar.gz -C dist GSBWiFi
	@echo "Oluşturuldu: release/GSBWiFi-linux.tar.gz"

clean:
	rm -rf dist/ build/ release/
	rm -f GSBWiFi-macos.dmg GSBWiFi-windows.zip
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
