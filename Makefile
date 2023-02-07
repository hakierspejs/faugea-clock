PORT=/dev/tty.usbmodem101
ifeq (,$(wildcard /dev/tty.usbmodem101))
	PORT=/dev/tty.usbmodem1101
endif

shell:
	mpremote connect $(PORT) repl

ls:
	mpremote connect $(PORT) ls

install_requirements:
	for id in $$(cat requirements.txt); do \
		mpremote connect $(PORT) mip install $$id; \
	done

rm_wifi_credentials:
	mpremote connect /dev/tty.usbmodem101 fs rm wifi.secrets

WIFI_INFO := $(shell mpremote connect $(PORT) fs cat ./wifi.secrets > /dev/null; echo $$?)
burn: install_requirements
ifneq ($(WIFI_INFO),0)
	mpremote connect $(PORT) fs cp wifi.secrets.example :wifi.secrets
	EDITOR=vim mpremote connect $(PORT) edit wifi.secrets
endif
	mpremote connect $(PORT) fs cp ./*.py :
	echo 'WIFI SSID:'; mpremote connect $(PORT) cat wifi.secrets | head -n1

run: burn
	mpremote connect $(PORT) run main.py

black:
	black ./*.py

