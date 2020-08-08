# chFlasher


### The chFlasher is a short python script to flash the cheap CH55x Microcontroller from the company WCH via command line interface.

It is compatible with these micros: CH551, CH552, CH554, CH558 and CH559

This short tool can flash the CH55x series with bootloader version 1.1 2.31 and 2.40.

Run this tool via the filename and plus the bin file you want to flash example:
```
ch55xV2flasher.py blink.bin
```

Copyright by Aaron Christophel [ATCnetz.de](https://ATCnetz.de) and [youtube/1200230](https://www.youtube.com/user/12002230/) you can edit and use this code as you want if you mention me :)

You can find a video manual on youtube from me:(click on the picture)
[![YoutubeVideo](https://img.youtube.com/vi/uhSHcyjUaic/0.jpg)](https://www.youtube.com/watch?v=uhSHcyjUaic)


you need to install python2.7 or python3 and pyusb to use this flasher or use the compiled exe
install it via:
```
pip install pyusb
```

on linux run: 
```
sudo apt-get install python-pip
sudo pip install pyusb
```

on windows you need the [zadig tool](https://zadig.akeo.ie/) to install the right driver
click on Options and List all devices to show the USB Module, then install the libusb-win32 driver for the CH chip
