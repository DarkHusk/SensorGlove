import dbus
import dbus.service
import struct
from hid_descriptor import HID_DESCRIPTOR

UUID_HID_SERVICE = "00001812-0000-1000-8000-00805f9b34fb"
UUID_REPORT_MAP = "00002A4B-0000-1000-8000-00805f9b34fb"
UUID_REPORT = "00002A4D-0000-1000-8000-00805f9b34fb"
UUID_HID_INFO = "00002A4A-0000-1000-8000-00805f9b34fb"
UUID_HID_CTRL = "00002A4C-0000-1000-8000-00805f9b34fb"
UUID_PROTO_MODE = "00002A4E-0000-1000-8000-00805f9b34fb"
UUID_REPORT_REF = "00002908-0000-1000-8000-00805f9b34fb"
UUID_CCCD = "00002902-0000-1000-8000-00805f9b34fb"
UUID_PNP_ID = "00002A50-0000-1000-8000-00805f9b34fb"

class HIDService(dbus.service.Object):
    PATH_BASE = "/aei/glove/hid/service"

    def __init__(self, bus, index):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = UUID_HID_SERVICE
        self.primary = True

        self.input_report = HIDInputReport(bus, 0, self)

        super().__init__(bus, self.path)

        self.characteristics = []
        self.add_characteristic(HIDInformation(bus, 0, self))
        self.add_characteristic(HIDControlPoint(bus, 1, self))
        self.add_characteristic(HIDProtocolMode(bus, 2, self))
        self.add_characteristic(HIDReportMap(bus, 3, self))
        self.add_characteristic(HIDPnPID(bus, 4, self))
        self.add_characteristic(self.input_report)

    def add_characteristic(self, chrc):
        self.characteristics.append(chrc)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {"org.bluez.GattService1": {"UUID": self.uuid, "Primary": dbus.Boolean(self.primary)}}

# ------------------ HID Characteristics ------------------

class HIDReportMap(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = f"{service.path}/char{index}"
        self.service = service
        self.uuid = UUID_REPORT_MAP
        self.flags = ["read"]
        super().__init__(bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {"org.bluez.GattCharacteristic1": {"Service": self.service.get_path(),
                                                  "UUID": self.uuid,
                                                  "Flags": dbus.Array(self.flags, signature="s")}}

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        return dbus.ByteArray(HID_DESCRIPTOR)

class ReportReferenceDescriptor(dbus.service.Object):
    def __init__(self, bus, index, characteristic):
        self.path = f"{characteristic.path}/desc{index}"
        self.characteristic = characteristic
        self.uuid = UUID_REPORT_REF
        self.value = dbus.ByteArray([0x01, 0x01])  # Report ID 1, Input
        super().__init__(bus, self.path)

    def get_properties(self):
        return {"org.bluez.GattDescriptor1": {"Characteristic": self.characteristic.get_path(),
                                             "UUID": self.uuid,
                                             "Flags": dbus.Array(["read"], signature="s")}}

    @dbus.service.method("org.bluez.GattDescriptor1", in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        return dbus.ByteArray(self.value)

class ClientCharacteristicConfigurationDescriptor(dbus.service.Object):
    def __init__(self, bus, index, characteristic):
        self.path = f"{characteristic.path}/desc_cccd{index}"
        self.characteristic = characteristic
        self.uuid = UUID_CCCD
        self.value = [0x00, 0x00]
        super().__init__(bus, self.path)

    def get_properties(self):
        return {"org.bluez.GattDescriptor1": {"Characteristic": self.characteristic.get_path(),
                                             "UUID": self.uuid,
                                             "Flags": dbus.Array(["read","write"], signature="s")}}

    @dbus.service.method("org.bluez.GattDescriptor1", in_signature="ay", out_signature="")
    def WriteValue(self, value):
        self.value = list(value)
        notify_enabled = self.value[0] & 0x01
        self.characteristic.notifying = bool(notify_enabled)
        print("Notifications enabled:", self.characteristic.notifying)

class HIDInputReport(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = f"{service.path}/char{index}"
        self.service = service
        self.uuid = UUID_REPORT
        self.flags = ["read","notify"]
        self.notifying = False
        super().__init__(bus, self.path)

        self.report_ref = ReportReferenceDescriptor(bus, 0, self)
        self.cccd = ClientCharacteristicConfigurationDescriptor(bus, 0, self)
        self.descriptors = [self.report_ref, self.cccd]

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {"org.bluez.GattCharacteristic1": {"Service": self.service.get_path(),
                                                  "UUID": self.uuid,
                                                  "Flags": dbus.Array(self.flags, signature="s")}}

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        report = struct.pack("<5h", 0,0,0,0,0)
        return dbus.ByteArray([0x01]+list(report))  # Report ID + 5 axes

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="", out_signature="")
    def StartNotify(self):
        self.notifying = True
        print("StartNotify called")

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="", out_signature="")
    def StopNotify(self):
        self.notifying = False

    def send_report(self, axes, button=0):
        if not self.notifying:
            return
        report_id = 0x01
        # button = 0 (released) or 1 (pressed)
        report = bytes([button & 0x01]) + struct.pack("<5h", *axes)
        print("REPORT LENGTH:", len(report), "BYTES:", list(report))
        self.PropertiesChanged("org.bluez.GattCharacteristic1",
                       {"Value": dbus.Array([dbus.Byte(b) for b in report], signature="y")}, [])

    @dbus.service.signal("org.freedesktop.DBus.Properties", signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

# ------------------ Standard Characteristics ------------------

class HIDInformation(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = f"{service.path}/char_info{index}"
        self.service = service
        self.uuid = UUID_HID_INFO
        self.flags = ["read"]
        super().__init__(bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {"org.bluez.GattCharacteristic1": {"Service": self.service.get_path(),
                                                  "UUID": self.uuid,
                                                  "Flags": dbus.Array(self.flags, signature="s")}}

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        return dbus.ByteArray([0x11,0x01,0x00,0x00])  # HID ver 1.11, country code 0, flags

class HIDControlPoint(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = f"{service.path}/char_ctrl{index}"
        self.service = service
        self.uuid = UUID_HID_CTRL
        self.flags = ["write-without-response"]
        super().__init__(bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {"org.bluez.GattCharacteristic1": {"Service": self.service.get_path(),
                                                  "UUID": self.uuid,
                                                  "Flags": dbus.Array(self.flags, signature="s")}}

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="ay", out_signature="")
    def WriteValue(self, value):
        print("Control Point written:", list(value))

class HIDProtocolMode(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = f"{service.path}/char_mode{index}"
        self.service = service
        self.uuid = UUID_PROTO_MODE
        self.flags = ["read","write-without-response"]
        self.mode = 1
        super().__init__(bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {"org.bluez.GattCharacteristic1": {"Service": self.service.get_path(),
                                                  "UUID": self.uuid,
                                                  "Flags": dbus.Array(self.flags, signature="s")}}

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        return dbus.ByteArray([self.mode])

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="ay", out_signature="")
    def WriteValue(self, value):
        self.mode = value[0]
        print("Protocol Mode set to", self.mode)

class HIDPnPID(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = f"{service.path}/char_pnp{index}"
        self.service = service
        self.uuid = UUID_PNP_ID
        self.flags = ["read"]
        super().__init__(bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {"org.bluez.GattCharacteristic1": {"Service": self.service.get_path(),
                                                  "UUID": self.uuid,
                                                  "Flags": dbus.Array(self.flags, signature="s")}}

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        return dbus.ByteArray([0x01,0x00,0x00,0x01,0x00,0x00,0x01])
