#!/usr/bin/env python3
import asyncio
import json
import sys

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
from dbus_next.message import Message

MATCH = "type='method_call',interface='org.freedesktop.Notifications',member='Notify'"
DBUS_NAME = "org.freedesktop.DBus"
DBUS_PATH = "/org/freedesktop/DBus"


async def main():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()

    introspect = await bus.introspect(DBUS_NAME, DBUS_PATH)
    mon = bus.get_proxy_object(DBUS_NAME, DBUS_PATH, introspect)
    monitoring = mon.get_interface(DBUS_NAME + ".Monitoring")
    await monitoring.call_become_monitor([MATCH], 0)

    def on_msg(msg: Message):
        if msg.member != "Notify":
            return
        a = msg.body
        out = {
            "appName": a[0],
            "replacesId": a[1],
            "appIcon": a[2],
            "summary": a[3],
            "body": a[4],
            "actions": a[5],
            "expireTimeout": a[7],
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    bus.add_message_handler(on_msg)
    await bus.wait_for_disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
