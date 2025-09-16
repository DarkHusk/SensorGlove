# Sensor Glove

A glove able to detect finger curls and hand position

## Used components
- Raspberrypi Zero 2 W
- MCP3008 ADC
- SparkFun SEN-08606 Flex Sensors

## Tasks

- [x] Reading flex sensors
- [x] HID comunication over BLE
- [ ] Dynamic calibration
- [ ] Detecting position and rotation

## Bluetooth Setup

```sudo systemctl edit bluetooth```

add those lines:

```
[Service]
ExecStart=
ExecStart=/usr/libexec/bluetooth/bluetoothd --experimental
```

next edit BlueZ config file using any text editor:

```sudo nano /etc/bluetooth/main.conf```

make sure you have:

```
[General]
Class = 0x200504
Passkey = 0000
DisablePlugins = a2dp,avrcp,sap,network,deviceinfo,volume
DiscoverableTimeout = 0
AlwaysPairable = true
PairableTimeout = 0
ControllerMode = le
JustWorksRepairing = always
```

to save in nano:

```ctrl + o -> enter -> ctrl + x```

then reboot Raspberrypi:

```sudo reboot now```