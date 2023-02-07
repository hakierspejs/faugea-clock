# FauGeA-clock

It allows you to turn an old VGA monitor into the wall clock with NTP time synchronization.

![](https://hssi.hs-ldz.pl/640x/http://server/img/1736459728345.jpeg)

VGA wires connection accordingly https://github.com/hakierspejs/pico-vga-driver 
Optionally, a buzzer could be connected to GPIO-6 (over NPN-transistor).

To run it locally you need Pico W with micropython.

Clone the repo:
```bash
git clone https://github.com/hakierspejs/faugea-clock

cd faugea-clock
```

Now you may use make commands to configure wifi and program PicoW:

```
make run

```

--------
Fell free to contribute


