#!/usr/bin/env python3

# this short tool can flash the CH55x series with bootloader version 1.1 and 2.31
# run this tool via the filename and plus the bin file you want to flash example: 
# ch55xV2flasher.py blink.bin

# support for: CH551, CH552, CH554, CH558 and CH559

# Copyright by https://ATCnetz.de (Aaron Christophel) you can edit and use this code as you want if you mention me :)

# now works with Python 2.7 or Python 3 thanks to adlerweb
# you need to install pyusb to use this flasher install it via pip install pyusb
# on linux run: sudo apt-get install python-pip and sudo pip install pyusb
# on windows you need the zadig tool https://zadig.akeo.ie/ to install the right driver
# click on Options and List all devices to show the USB Module, then install the libusb-win32 driver

import usb.core, usb.util, sys, struct, traceback, platform
detect_chip_cmd_v1 = (0xa2, 0x13, 0x55, 0x53, 0x42, 0x20, 0x44, 0x42, 0x47, 0x20, 0x43, 0x48, 0x35, 0x35, 0x39, 0x20, 0x26, 0x20, 0x49, 0x53, 0x50, 0x00)
detect_chip_cmd_v2 = (0xa1, 0x12, 0x00, 0x52, 0x11, 0x4d, 0x43, 0x55, 0x20, 0x49, 0x53, 0x50, 0x20, 0x26, 0x20, 0x57, 0x43, 0x48, 0x2e, 0x43, 0x4e)

device_erase_size = 8
device_flash_size = 16
chipid = 0

mode_write_v1 = 0xa8
mode_verify_v1 = 0xa7
mode_write_v2 = 0xa5
mode_verify_v2 = 0xa6

dev = usb.core.find(idVendor = 0x4348, idProduct = 0x55e0)
if dev is None:
    print('No CH55x device found, check driver please')
    sys.exit()

try:
    dev.set_configuration()
except usb.core.USBError as ex:
    print('Could not access USB Device')

    if str(ex).startswith('[Errno 13]') and platform.system() == 'Linux':
        print('No access to USB Device, configure udev or execute as root (sudo)')
        print('For udev create /etc/udev/rules.d/99-ch55x.rules')
        print('with one line:')
        print('---')
        print('SUBSYSTEM=="usb", ATTR{idVendor}=="4348", ATTR{idProduct}=="55e0", MODE="666"')
        print('---')
        print('Restart udev: sudo service udev restart')
        print('Reconnect device, should work now!')
        sys.exit(2)

    traceback.print_exc()
    sys.exit(2)


cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

epout = usb.util.find_descriptor(intf, custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
epin = usb.util.find_descriptor(intf, custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

assert epout is not None
assert epin is not None

def errorexit(errormsg):
    print('Error: ' + errormsg)
    sys.exit(1)

def sendcmd(cmd):
    epout.write(cmd)
    b = epin.read(64)
    return b

def detectchipversion():
    identanswer = sendcmd(detect_chip_cmd_v2)
    if len(identanswer) == 0:
        errorexit('USB Error')
    if len(identanswer) == 2:
        return 0
    else:
        return 1    

def erasechipv1():
    sendcmd((0xa6, 0x04, 0x00, 0x00, 0x00, 0x00))
    for x in range(device_flash_size):
        buffer = sendcmd((0xa9, 0x02, 0x00, x * 4))
        if buffer[0] != 0x00:
            errorexit('Erase Failed')
    print('Flash Erased')
        
def erasechipv2():
    buffer = sendcmd((0xa4, 0x01, 0x00, device_erase_size))
    if buffer[4] != 0x00:
        errorexit('Erase Failed')
    print('Flash Erased')

def exitbootloaderv1():
    epout.write((0xa5, 0x02, 0x01, 0x00))

def exitbootloaderv2():
    epout.write((0xa2, 0x01, 0x00, 0x01))

def identchipv1():
    global chipid,device_flash_size,device_erase_size
    identanswer = sendcmd(detect_chip_cmd_v1)
    if len(identanswer) == 2:
        chipid = identanswer[0]
        print('Found CH5' + str(chipid - 30))
        if chipid == 0x58:
            device_flash_size = 64
            device_erase_size = 11
        elif chipid == 0x59:
            device_flash_size = 64
            device_erase_size = 11
    else:
        errorexit('ident chip')
    cfganswer = sendcmd((0xbb, 0x00))
    if len(cfganswer) == 2:
        print('Bootloader version: ' + str((cfganswer[0] >> 4)) + '.' + str((cfganswer[0] & 0xf)))
    else:
        errorexit('ident bootloader')

def identchipv2():
    global chipid, device_flash_size, device_erase_size
    identanswer = sendcmd(detect_chip_cmd_v2)
    if len(identanswer) == 6:
        chipid = identanswer[4]
        print('Found CH5' + str(chipid - 30))
        if chipid == 0x58:
            device_flash_size = 64
            device_erase_size = 11
        elif chipid == 0x59:
            device_flash_size = 64
            device_erase_size = 11
    else:
        errorexit('ident chip')
    cfganswer = sendcmd((0xa7, 0x02, 0x00, 0x1f, 0x00))
    if len(cfganswer) == 30:
        print('Bootloader version: ' + str(cfganswer[19]) + '.' + str(cfganswer[20]) + str(cfganswer[21]))
        keyinputv2(cfganswer)
    else:
        errorexit('ident bootloader')

def keyinputv2(cfganswer):
    outbuffer = bytearray(64)
    outbuffer[0] = 0xa3
    outbuffer[1] = 0x30
    outbuffer[2] = 0x00
    checksum = cfganswer[22]
    checksum += cfganswer[23]
    checksum += cfganswer[24]
    checksum += cfganswer[25]
    for x in range(0x30):
        outbuffer[x+3] = checksum & 0xff
    sendcmd(outbuffer)

def writefilev1(fileName, mode):
    global chipid
    bytes = open(fileName, 'rb').read()
    if mode == mode_write_v1:
        print('Filesize: ' + str(len(bytes)) + ' bytes')
    i = len(bytes)
    curr_addr = 0
    pkt_length = 0
    while curr_addr < len(bytes):
        outbuffer = bytearray(64)
        if i >= 0x3c:
            pkt_length = 0x3c
        else:
            pkt_length = i
        outbuffer[0] = mode
        outbuffer[1] = pkt_length
        outbuffer[2] = (curr_addr & 0xff)
        outbuffer[3] = ((curr_addr >> 8) & 0xff)
        for x in range(pkt_length):
            outbuffer[x + 4] = bytes[curr_addr + x]
        #print(''.join('{:02x}'.format(x) for x in outbuffer))
        buffer = sendcmd(outbuffer)
        curr_addr += pkt_length
        i -= pkt_length
        if buffer != None:
            if buffer[0] != 0x00:
                if mode == mode_write_v1:
                    errorexit('Write Failed!!!')
                elif mode == mode_verify_v1:
                    errorexit('Verify Failed!!!')
    if mode == mode_write_v1:
        print('Writing success')
    elif mode == mode_verify_v1:
        print('Verify success')

def writefilev2(fileName, mode):
    global chipid
    bytes = open(fileName, 'rb').read()
    if mode == mode_write_v2:
        print('Filesize: ' + str(len(bytes)) + ' bytes')
    if len(bytes) < 256:
        errorexit('Something wrong with the bin file')
    i = len(bytes)
    curr_addr = 0
    pkt_length = 0
    while curr_addr < len(bytes):
        outbuffer = bytearray(64)
        if i >= 0x38:
            pkt_length = 0x38
        else:
            pkt_length = i
        outbuffer[0] = mode
        outbuffer[1] = (pkt_length+5)
        outbuffer[2] = 0x00
        outbuffer[3] = (curr_addr & 0xff)
        outbuffer[4] = ((curr_addr >> 8) & 0xff)
        outbuffer[5] = 0x00
        outbuffer[6] = 0x00
        outbuffer[7] = i & 0xff
        for x in range(pkt_length):
            outbuffer[x + 8] = bytes[curr_addr + x]
        for x in range(pkt_length + 8):
            if x % 8 == 7:
                outbuffer[x] ^= chipid
        #print(''.join('{:02x}'.format(x) for x in outbuffer))
        buffer = sendcmd(outbuffer)
        curr_addr += pkt_length
        i -= pkt_length
        if buffer != None:
            if buffer[4] != 0x00 and buffer[4] != 0xfe and buffer[4] != 0xf5:
                if mode == mode_write_v2:
                    errorexit('Write Failed!!!')
                elif mode == mode_verify_v2:
                    errorexit('Verify Failed!!!')
    if mode == mode_write_v2:
        print('Writing success')
    elif mode == mode_verify_v2:
        print('Verify success')
    
if len(sys.argv) != 2:
    errorexit('no bin file selected')   
    
if detectchipversion() == 0:
    identchipv1()
    erasechipv1()
    writefilev1(sys.argv[1], mode_write_v1)
    writefilev1(sys.argv[1], mode_verify_v1)
    exitbootloaderv1()
else:
    identchipv2()
    erasechipv2()
    writefilev2(sys.argv[1], mode_write_v2)
    writefilev2(sys.argv[1], mode_verify_v2)
    exitbootloaderv2()

