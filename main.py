# Implementation of module for command line.
# The module can be tested by running the following command:
# `python3 -m pyisy http://your-isy-url:80 username password`
# Use `python3 -m pyisy -h` for full usage information.
# This script can also be copied and used as a template for
# using this module.

import os
import argparse
import asyncio
import logging
import time
from urllib.parse import urlparse
from dotenv import load_dotenv


from pyisy import ISY
from pyisy.connection import ISYConnectionError, ISYInvalidAuthError, get_new_client_session
from pyisy.constants import NODE_CHANGED_ACTIONS, SYSTEM_STATUS
from pyisy.logging import LOG_VERBOSE, enable_logging
from pyisy.nodes import NodeChangedEvent

_LOGGER = logging.getLogger(__name__)

load_dotenv()
URL = os.getenv("URL")
NAME_LOCAL = os.getenv("USER_NAME")
PASS = os.getenv("PASS")

async def main(url, username, password, tls_ver, events, node_servers):
    # Execute connection to ISY and load all system info.
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
        # _LOGGER.error("Unknown error occurred: %s", err.args[0])
        await isy.shutdown()
        raise

    # Print a representation of all the Nodes
    # _LOGGER.debug(repr(isy.nodes))
    # _LOGGER.info("Total Loading time: %.2fs", time.time() - t_0)

    node_changed_subscriber = None
    system_status_subscriber = None


    def node_changed_handler(event: NodeChangedEvent) -> None:
        # Handle a node changed event sent from Nodes class.
        (event_desc, _) = NODE_CHANGED_ACTIONS[event.action]
        _LOGGER.info(
            "Subscriber--Node %s Changed: %s %s",
            event.address,
            event_desc,
            event.event_info if event.event_info else "",
        )

    def system_status_handler(event: str) -> None:
        # Handle a system status changed event sent ISY class.
        _LOGGER.info("System Status Changed: %s", SYSTEM_STATUS.get(event))

    async def nookRamp():
        NODE = "1A 18 EA 1"
        scene = isy.nodes["Kitchen"]["Scenes"]["12520"]
        node = isy.nodes["Kitchen"]["Z_Keypads"][NODE]
        await node.turn_on(count)
        count += 5
        print(count)
        if count >= 150:
            count = 0
        await asyncio.sleep(1)

    async def ventControlNook():
        # print(repr(isy.variables))

        l1 = int(isy.variables[2][24].status)
        l2 = int(isy.variables[2][25].status)
        l3 = int(isy.variables[2][26].status)
        l4 = int(isy.variables[2][27].status)
        print("L1: "+ str(l1))
        print("L2: "+ str(l2))
        print("L3: "+ str(l3))
        print("L4: "+ str(l4))

        NOOK = "1A 18 EA 1"
        node = isy.nodes["Kitchen"]["Z_Keypads"][NOOK]
        MULTIPIER = 63
        brightness = (l1 + l2 + l3 + l4) * MULTIPIER
        print(brightness)
        
        await node.turn_on(brightness)

        

    count = 0 
    # NODE = "1A 18 EA 1"
    # node = isy.nodes["Kitchen"]["Z_Keypads"][NODE]
    # await node.turn_off()
    try:
        if events:
            isy.websocket.start()

            node_changed_subscriber = isy.nodes.status_events.subscribe(node_changed_handler)
            system_status_subscriber = isy.status_events.subscribe(system_status_handler)
        while True:
            print("i got here")
            # print(repr(isy.nodes))
            # print("i printed nodes")
            # await nookRamp()
            await ventControlNook()
            await asyncio.sleep(2)
            
    except asyncio.CancelledError:
        pass
    finally:
        if node_changed_subscriber:
            node_changed_subscriber.unsubscribe()
        if system_status_subscriber:
            system_status_subscriber.unsubscribe()
        await isy.shutdown()


if __name__ == "__main__":

    # enable_logging(LOG_VERBOSE if args.verbose else logging.DEBUG)

    _LOGGER.info(
        "ISY URL: %s, username: %s, TLS: %s",
        URL,
        NAME_LOCAL,
        "1.1"
    )

    try:
        asyncio.run(
            main(
                url= URL,
                username=NAME_LOCAL,
                password=PASS,
                tls_ver='1.1',
                events=True,
                node_servers=False,

            )
        )
    except KeyboardInterrupt:
        _LOGGER.warning("KeyboardInterrupt received. Disconnecting!")
