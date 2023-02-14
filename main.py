import gc
import utime
import _thread
import ntptime
import network
from machine import Pin, PWM, WDT, reset as machine_reset

from segclock import Clock
from vga_driver import TinyVgaDriver

from logo import draw_logo
from timezone import get_current_timezone


WIFI_THREAD_OUTPUT = ""

WLAN = network.WLAN(network.STA_IF)

TIME_ACTUALIZED = 0

PIN_BUZZER = Pin(18, Pin.OUT)

WATCHDOG = WDT(timeout=6000)  # s

VGA = TinyVgaDriver()


def sleep_ms(ms):
    global WATCHDOG
    WATCHDOG.feed()
    utime.sleep_ms(500)
    return


def _load_wifi_credentials():
    with open("wifi.secrets") as secrets:
        lines = secrets.readlines()
        ssid = lines[0].strip()
        passwd = lines[1][:-1]
    return (ssid, passwd)


def wifi_connect():
    global WATCHDOG
    printout_text("connecting to wifi")
    WLAN.active(True)
    ssid, passwd = _load_wifi_credentials()
    WLAN.connect(ssid, passwd)

    for i in range(45):
        WATCHDOG.feed()
        if WLAN.status() != 3:
            utime.sleep_ms(1000)
            printout_text("connecting to wifi " + ssid + " " + "." * i)
        else:
            break
    # Handle connection error
    if WLAN.status() != 3:
        printout_text("Wifi connection failed")
        return None

    return WLAN


def wifi_disconnect():
    global WLAN
    WLAN.disconnect()
    WLAN.active(False)
    return


def printout_text(message):
    global WIFI_THREAD_OUTPUT
    print(message)
    WIFI_THREAD_OUTPUT = message


def get_local_datetime():
    timezone = get_current_timezone(utime.time())
    local_datetime = utime.gmtime()
    hh = local_datetime[3] + timezone
    return (hh % 24, local_datetime[4], local_datetime[5])


def tone():
    global WATCHDOG
    for i in range(4):
        WATCHDOG.feed()
        PIN_BUZZER.high()
        utime.sleep_ms(100 - 10 * i)
        PIN_BUZZER.low()
        utime.sleep_ms(100 + 100 * i)
    return


def redraw_messages(fbuf, message, need_hide_wifi_output=False):
    output_offset_x = 10
    output_offset_y = 480 - 8 - 10
    if message:
        fbuf.rect(output_offset_x, output_offset_y, 640, 8, VGA.COLOR_BLACK, True)
        fbuf.text(message, output_offset_x, output_offset_y)
    elif need_hide_wifi_output:
        fbuf.rect(output_offset_x, output_offset_y, 640, 8, VGA.COLOR_BLACK, True)


def vga_thread(job):
    global WATCHDOG
    global WIFI_THREAD_OUTPUT
    global TIME_ACTUALIZED

    WATCHDOG.feed()

    fbuf = VGA.start_synchronisation()

    clock = Clock(
        fbuf,
        VGA.resolution_horisontal,
        VGA.resolution_vertical,
        offset_x=10,
        offset_y=140,
        scale_x=17,
        scale_y=17,
    )
    offset_x = 120
    offset_y = 40

    fbuf.fill(VGA.COLOR_BLACK)

    need_hide_wifi_output = False

    fbuf.text("Hackerspace Lodz - faugea-clock", 180, 16, VGA.COLOR_RED)

    WATCHDOG.feed()
    draw_logo(VGA, fbuf, offset_x, offset_y)

    while not TIME_ACTUALIZED:
        sleep_ms(500)
        if WIFI_THREAD_OUTPUT:
            redraw_messages(fbuf, WIFI_THREAD_OUTPUT, need_hide_wifi_output)

    fbuf.fill(VGA.COLOR_BLACK)
    fbuf.text("Hackerspace Lodz - faugea-clock", 180, 16, VGA.COLOR_RED)

    sleep_ms(100)
    clock.draw(88, 88, colon=True)
    sleep_ms(100)

    hh, mm, ss = 0, 0, 0
    for i in range(3600 * 24 * 100):
        # print('ping ', i)
        if TIME_ACTUALIZED:
            hh, mm, ss = get_local_datetime()
            clock.draw(hh, mm, colon=False)

            sleep_ms(500)
            clock.draw(hh, mm, colon=True)

        if WIFI_THREAD_OUTPUT:
            redraw_messages(fbuf, WIFI_THREAD_OUTPUT, need_hide_wifi_output)
            need_hide_wifi_output = True
        elif need_hide_wifi_output:
            redraw_messages(fbuf, WIFI_THREAD_OUTPUT, need_hide_wifi_output)
            need_hide_wifi_output = False

        sleep_ms(500)
        gc.collect()

        if hh == 3 and mm == 14:
            VGA.stop_synchronisation()

            sleep_ms(1 * 1000)

            machine_reset()

        if TIME_ACTUALIZED and mm == 0:
            tone()

    VGA.stop_synchronisation()
    utime.sleep_ms(1 * 1000)


def main():
    global TIME_ACTUALIZED

    tone()
    _thread.start_new_thread(vga_thread, (1,))

    for i in range(1000000):
        try:
            result = wifi_connect()

            if result is None:
                utime.sleep_ms(5 * 1000)
                VGA.stop_synchronisation()
                machine_reset()

            printout_text("WIFI connected IP:" + str(WLAN.ifconfig()[0]))

            ntptime.settime()  # update time
            tone()
            TIME_ACTUALIZED = True

            wifi_disconnect()

            printout_text("WIFI disconnected; Time is synchronized.")

            utime.sleep_ms(10 * 1000)

            printout_text("")
        except OSError as e:
            printout_text("ERROR: " + str(e))
            print(e)
            utime.sleep_ms(5 * 1000)
            try:
                wifi_disconnect()
                printout_text("WIFI disconnected")
                utime.sleep_ms(60 * 1000)
            except Exception as e:
                pass
            utime.sleep_ms(5 * 60 * 1000)
            if not TIME_ACTUALIZED:
                machine_reset()
        else:
            utime.sleep_ms(3 * 3600 * 1000)


if __name__ == "__main__":
    main()
