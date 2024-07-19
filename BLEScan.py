"""
Scan/Discovery
--------------
Example showing how to scan for BLE devices.
Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>
"""
import asyncio
from bleak import discover

async def get_ble_device_address(device_name):
    devices = await discover()
    for d in devices:
        # print(d.name, d.address)
        if d.name == device_name:
        # if d.address == device_name:
            return d.address
    return None

# # added by jyoh
# if __name__ == "__main__":
#     # device_name = "06:8E:F2:30:22:4D"
#     device_name = "7C:50:79:6C:21:F8"
#     # EB_00068EF230224D C0:3C:1C:40:00:EB


#     asyncio.run(get_ble_device_address(device_name))