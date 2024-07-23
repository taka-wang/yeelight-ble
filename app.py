import asyncio
import struct
import logging
from bleak import BleakClient, BleakScanner
from aiohttp import web
import os

logger = logging.getLogger(__name__)

NOTIFY_UUID = "8f65073d-9f57-4aaa-afea-397d19d5bbeb"
CONTROL_UUID = "aa7d3f34-2d4f-41e0-807f-52fbf8cf7443"
MAC_ADDRESS = "f8:24:41:e4:62:9f"

COMMAND_STX = 0x43
CMD_PAIR = 0x67
CMD_PAIR_ON = 0x02
CMD_POWER = 0x40
CMD_POWER_ON = 0x01
CMD_POWER_OFF = 0x02
CMD_GETSTATE = 0x44
CMD_GETSTATE_SEC = 0x02
CMD_BRIGHTNESS = 0x42

class YeelightBedside:
    def __init__(self, address="f8:24:41:e4:62:9f"):
        if not address:
            raise ValueError("Address must be provided")
        self.address = address
        self.client = None
        self.is_on = False
        self.brightness = 0
        self.paired = False

    async def connect(self, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Scanning for device {self.address}...")
                device = await BleakScanner.find_device_by_address(self.address, timeout=20.0)
                if not device:
                    raise Exception(f"Device {self.address} not found")
                
                logger.debug(f"Device found. Attempting to connect... (Attempt {attempt + 1}/{max_attempts})")
                self.client = BleakClient(device)
                await self.client.connect()
                
                logger.debug("Connected. Starting notification...")
                await self.client.start_notify(NOTIFY_UUID, self.notification_handler)
                
                if not self.paired:
                    # logger.info("Initiating pairing...")
                    await self.pair()
                    self.paired = True
                
                logger.debug("Connection successful!")
                return
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if self.client:
                    await self.client.disconnect()
                if attempt == max_attempts - 1:
                    raise

    async def pair(self):
        bits = struct.pack("BBB15x", COMMAND_STX, CMD_PAIR, CMD_PAIR_ON)
        await self.client.write_gatt_char(CONTROL_UUID, bits)

    async def turn_on(self):
        bits = struct.pack("BBB15x", COMMAND_STX, CMD_POWER, CMD_POWER_ON)
        await self.client.write_gatt_char(CONTROL_UUID, bits)
        logger.debug("Turn on command sent")

    async def turn_off(self):
        bits = struct.pack("BBB15x", COMMAND_STX, CMD_POWER, CMD_POWER_OFF)
        await self.client.write_gatt_char(CONTROL_UUID, bits)
        logger.debug("Turn off command sent")

    async def get_state(self):
        bits = struct.pack("BBB15x", COMMAND_STX, CMD_GETSTATE, CMD_GETSTATE_SEC)
        await self.client.write_gatt_char(CONTROL_UUID, bits)
        logger.debug("Get state command sent")

    async def set_brightness(self, brightness):
        brightness = max(1, min(100, brightness))  # Ensure brightness is between 1 and 100
        bits = struct.pack("BBB15x", COMMAND_STX, CMD_BRIGHTNESS, brightness)
        await self.client.write_gatt_char(CONTROL_UUID, bits)
        logger.debug(f"Set brightness command sent: {brightness}")

    def notification_handler(self, sender, data):
        logger.debug(f"Received: {data.hex()}")
        if len(data) > 2 and data[1] == 0x45:  # RES_GETSTATE
            state = struct.unpack(">xxBBBBBBBhx6x", data)
            self.is_on = state[0] == CMD_POWER_ON
            self.brightness = state[6]
            logger.info(f"Lamp is {'ON' if self.is_on else 'OFF'}, brightness: {self.brightness}")

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()

class AppState:
    def __init__(self):
        self.lamp = None
        self.connected = False

app_state = AppState()

async def handle_request(request):
    command = request.match_info.get('command', 'status')
    if not app_state.connected:
        try:
            app_state.lamp = YeelightBedside(MAC_ADDRESS)
            await app_state.lamp.connect()
            app_state.connected = True
        except Exception as e:
            return web.Response(text=f"Failed to connect to the lamp: {str(e)}", status=500)

    try:
        if command == 'on':
            await app_state.lamp.turn_on()
            return web.Response(text="Lamp turned ON")
        elif command == 'off':
            await app_state.lamp.turn_off()
            return web.Response(text="Lamp turned OFF")
        elif command == 'status':
            await app_state.lamp.get_state()
            state = 'ON' if app_state.lamp.is_on else 'OFF'
            return web.Response(text=f"Lamp is {state}, brightness: {app_state.lamp.brightness}")
        elif command == 'brightness':
            try:
                brightness = int(request.query['value'])
                brightness = max(1, min(100, brightness))  # Ensure brightness is between 1 and 100
                await app_state.lamp.set_brightness(brightness)
                app_state.lamp.brightness = brightness  # Update the stored brightness
                return web.Response(text=f"Brightness set to {brightness}")
            except (KeyError, ValueError):
                return web.Response(text="Invalid brightness command. Use 'brightness?value=XX' where XX is between 1 and 100.", status=400)
        elif command == 'up':
            new_brightness = min(100, app_state.lamp.brightness + 10)
            await app_state.lamp.set_brightness(new_brightness)
            app_state.lamp.brightness = new_brightness  # Update the stored brightness
            return web.Response(text=f"Brightness increased to {new_brightness}")
        elif command == 'down':
            new_brightness = max(1, app_state.lamp.brightness - 10)
            await app_state.lamp.set_brightness(new_brightness)
            app_state.lamp.brightness = new_brightness  # Update the stored brightness
            return web.Response(text=f"Brightness decreased to {new_brightness}")
        else:
            return web.Response(text="Unknown command", status=400)
    except Exception as e:
        return web.Response(text=str(e), status=500)

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get('/{command}', handle_request)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9090)
    await site.start()
    logger.info("Server started at http://0.0.0.0:9090")
    while True:
        await asyncio.sleep(3600)  # Run indefinitely

if __name__ == "__main__":
    asyncio.run(main())