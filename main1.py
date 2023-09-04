"""Implementation of module for command line.
The module can be tested by running the following command:
`python3 -m pyisy http://your-isy-url:80 username password`
Use `python3 -m pyisy -h` for full usage information.
This script can also be copied and used as a template for
using this module.
"""
import os
from dotenv import load_dotenv
import argparse
import asyncio
import logging
import time
from urllib.parse import urlparse
import json
from threading import Thread
# from fan import Fan, ExhuastFans
from color import color

from pyisy import ISY
from pyisy.connection import ISYConnectionError, ISYInvalidAuthError, get_new_client_session
from pyisy.constants import NODE_CHANGED_ACTIONS, SYSTEM_STATUS
from pyisy.logging import LOG_VERBOSE, enable_logging
from pyisy.nodes import NodeChangedEvent

load_dotenv()

ADDRESS = os.getenv("ADDRESS")
USERNAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")

_LOGGER = logging.getLogger(__name__)


async def main(url, username, password, tls_ver, events, node_servers):
    """Execute connection to ISY and load all system info."""
    _LOGGER.info("Starting PyISY...")
    t_0 = time.time()
    host = urlparse(url)
    if host.scheme == "http":
        https = False
        port = host.port or 80
    elif host.scheme == "https":
        https = True
        port = host.port or 443
    else:
        _LOGGER.error("host value in configuration is invalid.")
        return False

    # Use the helper function to get a new aiohttp.ClientSession.
    websession = get_new_client_session(https, tls_ver)

    # Connect to ISY controller.
    isy = ISY(
        host.hostname,
        port,
        username=username,
        password=password,
        use_https=https,
        tls_ver=tls_ver,
        webroot=host.path,
        websession=websession,
        use_websocket=True,
    )

    try:
        await isy.initialize(node_servers)
    except (ISYInvalidAuthError, ISYConnectionError):
        _LOGGER.error(
            "Failed to connect to the ISY, please adjust settings and try again."
        )
        await isy.shutdown()
        return
    except Exception as err:
        _LOGGER.error("Unknown error occurred: %s", err.args[0])
        await isy.shutdown()
        raise

    # Print a representation of all the Nodes
    # _LOGGER.debug(repr(isy.nodes))
    _LOGGER.info("Total Loading time: %.2fs", time.time() - t_0)

    node_changed_subscriber = None
    system_status_subscriber = None

    def node_changed_handler(event: NodeChangedEvent) -> None:
        """Handle a node changed event sent from Nodes class."""
        (event_desc, _) = NODE_CHANGED_ACTIONS[event.action]
        _LOGGER.info(
            "Subscriber--Node %s Changed: %s %s",
            event.address,
            event_desc,
            event.event_info if event.event_info else "",
        )

    def system_status_handler(event: str) -> None:
        """Handle a system status changed event sent ISY class."""
        _LOGGER.info("System Status Changed: %s", SYSTEM_STATUS.get(event))

    try:
        if events:
            isy.websocket.start()
            node_changed_subscriber = isy.nodes.status_events.subscribe(
                node_changed_handler
            )
            system_status_subscriber = isy.status_events.subscribe(
                system_status_handler
            )

        # isy.nodes["Crawlspace Exhaust Fan"].turn_on(5)
        while True:
            await asyncio.sleep(1)
            # await isy.nodes["Crawlspace Exhaust Fan"].turn_on(5)
            # await isy.nodes["Crawlspace Exhaust Fan"].turn_off()
            # print(isy.nodes["Crawlspace Exhaust Fan"].status)

            # print("N Bath Fan Status: " + str(isy.nodes["N Bath Fan"].status))
            # print("S Bath Fan Status: " + str(isy.nodes["S Bath Fan"].status))
            # print("Powder Fan Switch Status: " + str(isy.nodes["Powder Fan Switch"].status))
            #
            # print("-----------------------------------------")
            # print(isy.nodes["n002_48a2e62ce05605"].aux_properties["CLIHUM"].formatted)
            # print(isy.nodes["n002_48a2e62ce05605"].aux_properties["CLIHUM"].value)
            # print(isy.nodes["Double Bathroom"].aux_properties["CLIHUM"].value)
            # print(bool(isy.nodes["Double Bathroom"].aux_properties["GV3"].value))
            # print(isy.nodes["Double Bathroom"].aux_properties["GV4"].formatted)
            # isy.nodes["N Bath Fan"].turn_on(255)
            isy.nodes["N Bath Fan"].turn_off()
            print(isy.nodes["N Bath Fan"].status)
            # print(isy.)
            # print(isy.nodes["Guest Bathroom"].aux_properties["GV3"].formatted)
            # print(isy.nodes["Guest Bathroom"].aux_properties["GV4"].formatted)
            # print(repr(isy.variables))
            # print(isy.variables.get_by_name("IAQ On/Off").status)


            # with open("util.json", "r+") as file:
            #     file_data = json.load(file)
            #     for intake in file_data["supply_fan_names"]:
            #         node = isy.nodes[intake]
            #         file_data["supplies"][intake].update({"name":node.name})

            #     file.seek(0)
            #     json.dump(file_data, file, indent = 4)

        # exhuast_fansObject = ExhuastFans(isy, file_data.get("exhuast_fan_names"))
        # break
        # await asyncio.sleep(1)

        # exhuast_fansObject.update()
        # exhuast_fans = exhuast_fansObject.dict

        # cfm = await getExhuastCFM(exhuast_fans)

        # for exhuast_fan in exhuast_fans:
        #     fan = exhuast_fans[exhuast_fan]
        #     print(fan)

        # if cfm > 0 and

        # print("{}TOTAL EXHUAST CFM: {}{}".format(color.BOLD, cfm, color.END))
        # print(color.BOLD + time.ctime(time.time()) + color.END)
        # print("-----------------------------------------")



    except asyncio.CancelledError:
        pass
    finally:
        if node_changed_subscriber:
            node_changed_subscriber.unsubscribe()
        if system_status_subscriber:
            system_status_subscriber.unsubscribe()
        await isy.shutdown()


async def getExhuastCFM(exhuast_fans):
    cfm = 0
    for exhuast_fan in exhuast_fans:
        fan = exhuast_fans[exhuast_fan]
        # print(fan)

        if fan.type == "bool":
            cfm += fan.value and fan.cfm

        if fan.type == "255":
            ratio = 1 / 255
            cfm += round(fan.cfm * fan.value * ratio)

    return cfm


def openFreshAir(node):
    node.turn_on()
    asyncio.sleep(33)


def test(hello):
    print(hello)
    for i in range(1, 31):
        print(i)
        asyncio.sleep(1)


if __name__ == "__main__":

    enable_logging(logging.DEBUG)

    _LOGGER.info(
        "ISY URL: %s, username: %s, TLS: %s",
        ADDRESS,
        USERNAME,
    )

    try:
        asyncio.run(
            main(
                url=ADDRESS,
                username=USERNAME,
                password=PASSWORD,
                tls_ver=1.1,
                events=True,
                node_servers=False,
            )
        )
    except KeyboardInterrupt:
        _LOGGER.warning("KeyboardInterrupt received. Disconnecting!")
