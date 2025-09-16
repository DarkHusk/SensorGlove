import spidev

class MCP3008:
    def __init__(self, bus=0, device=0):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 1350000

    def read_channel(self, channel):
        """
        Read a single channel (0–7) from MCP3008.
        Returns value 0–1023.
        """
        if channel < 0 or channel > 7:
            raise ValueError("Invalid channel, must be 0–7")

        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        value = ((adc[1] & 3) << 8) + adc[2]
        return value

    def close(self):
        self.spi.close()


def read_flex_sensors():
    """
    Reads 5 flex sensors on CH0–CH4, scales to -32768 - 32767.
    """
    raw_min = 200
    raw_max = 400
    mcp = MCP3008()
    values = []
    for ch in range(5):
        raw = mcp.read_channel(ch)
        # Scale to -32768 - 32767 range
        scaled = int((raw - raw_min) * 65535 / (raw_max - raw_min) - 32768)
        scaled = max(-32768, min(32767, scaled))  # clamp
        values.append(scaled)
    mcp.close()
    return values