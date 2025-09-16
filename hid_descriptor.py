HID_DESCRIPTOR = bytes([
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x04,        # Usage (Joystick)
    0xA1, 0x01,        # Collection (Application)
        0x85, 0x01,    # Report ID 1

        0xA1, 0x00,    #Collection(Physical)
            # --- 1 button ---
            0x05, 0x09,    # Usage Page (Button)
            0x19, 0x01,    # Usage Minimum (Button 1)
            0x29, 0x01,    # Usage Maximum (Button 1)
            0x15, 0x00,    # Logical Minimum 0
            0x25, 0x01,    # Logical Maximum 1
            0x75, 0x01,    # Report Size: 1 bit
            0x95, 0x01,    # Report Count: 1
            0x81, 0x02,    # Input (Data,Var,Abs)
            0x75, 0x07,    # Padding 7 bits
            0x95, 0x01,
            0x81, 0x03,    # Input (Const,Var,Abs) - padding

            # --- 5 axes, 16-bit each ---
            0x05, 0x01,        # Usage Page (Generic Desktop)
            0x16, 0x00, 0x80,  # Logical Min: -32768
            0x26, 0xFF, 0x7F,  # Logical Max: 32767
            0x75, 0x10,        # Report Size: 16 bits
            0x95, 0x05,        # Report Count: 5 axes
            0x09, 0x30,        # Usage X
            0x09, 0x31,        # Usage Y
            0x09, 0x32,        # Usage Z
            0x09, 0x33,        # Usage Rx
            0x09, 0x34,        # Usage Ry
            0x81, 0x02,        # Input (Data,Var,Abs)

        0xC0,               # End Collection
    0xC0               # End Collection
])
