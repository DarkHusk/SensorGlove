import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import threading
import time

from gatt_server import HIDService
from sensors import read_flex_sensors
from advertisement import Advertisement
from agent import NoInputNoOutputAgent
from agent import AGENT_PATH

BLUEZ_SERVICE_NAME = "org.bluez"
ADAPTER_IFACE = "org.bluez.Adapter1"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"


class Application(dbus.service.Object):
    """
    GATT Application implementing ObjectManager so BlueZ
    can discover services and characteristics.
    """
    def __init__(self, bus):
        self.path = "/aei/glove/hid"
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def add_service(self, service):
        self.services.append(service)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_services(self):
        return self.services

    @dbus.service.method("org.freedesktop.DBus.ObjectManager",
                     out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        managed_objects = {}
        for service in self.services:
            managed_objects[service.get_path()] = service.get_properties()
            for chrc in service.characteristics:
                managed_objects[chrc.get_path()] = chrc.get_properties()
                if hasattr(chrc, "get_descriptors"):
                    for desc in chrc.get_descriptors():
                        managed_objects[desc.path] = desc.get_properties()
        return managed_objects



def sensor_loop(hid_service):
    """
    Background loop that reads flex sensors and sends HID reports.
    """
    while True:
        try:
            axes = read_flex_sensors()
            hid_service.input_report.send_report(axes)
        except Exception as e:
            print(f"Sensor error: {e}")
            axes = [0, 0, 0, 0, 0]
            hid_service.input_report.send_report(axes)
        time.sleep(0.05)  # 20 Hz update rate


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter_path = "/org/bluez/hci0"
    adapter_props = dbus.Interface(
    bus.get_object(BLUEZ_SERVICE_NAME, adapter_path),
    "org.freedesktop.DBus.Properties")

    # Make discoverable
    adapter_props.Set(ADAPTER_IFACE, "Discoverable", dbus.Boolean(True))
    adapter_props.Set(ADAPTER_IFACE, "Alias", "GloveJoystick")
    adapter_props.Set(ADAPTER_IFACE, "DiscoverableTimeout", dbus.UInt32(0))

    # Create GATT application
    app = Application(bus)

    # Add HID service
    hid_service = HIDService(bus, 0)
    app.add_service(hid_service)

    # Register GATT app
    gatt_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter_path),
        GATT_MANAGER_IFACE
    )
    gatt_manager.RegisterApplication(
        app.get_path(), 
        {"RequireAuthentication": dbus.Boolean(False),
         "RequireAuthorization": dbus.Boolean(False)},
        reply_handler=lambda: print("GATT application registered"),
        error_handler=lambda e: print("Failed to register application:", e)
    )

    # Register Advertisement
    ad_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter_path),
        LE_ADVERTISING_MANAGER_IFACE
    )
    advertisement = Advertisement(bus, 0, "peripheral")
    ad_manager.RegisterAdvertisement(
        advertisement.get_path(), {},
        reply_handler=lambda: print("Advertisement registered"),
        error_handler=lambda e: print("Failed to register advertisement:", e)
    )

    # Register NoInputNoOutput agent
    agent = NoInputNoOutputAgent(bus)
    agent_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez"),
        "org.bluez.AgentManager1"
    )
    agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")
    agent_manager.RequestDefaultAgent(AGENT_PATH)
    print("NoInputNoOutput agent registered")

    # Start sensor thread
    threading.Thread(target=sensor_loop, args=(hid_service,), daemon=True).start()

    print("Running HID joystick service...")
    loop = GLib.MainLoop()
    loop.run()


if __name__ == "__main__":
    main()
