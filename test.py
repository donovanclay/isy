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
from fan import Fan, ExhuastFan, ExhuastFans, SupplyFan, SupplyFans
from color import color

from pyisy import ISY
from pyisy.connection import ISYConnectionError, ISYInvalidAuthError, get_new_client_session
from pyisy.constants import NODE_CHANGED_ACTIONS, SYSTEM_STATUS
from pyisy.logging import LOG_VERBOSE, enable_logging
from pyisy.nodes import NodeChangedEvent

load_dotenv()

ADDRESS = os.getenv("ADDRESS")
USERNAME = os.getenv("USERNAME")
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
        # _LOGGER.info(
        #     "Subscriber--Node %s Changed: %s %s",
        #     event.address,
        #     event_desc,
        #     event.event_info if event.event_info else "",
        #     )

    def system_status_handler(event: str) -> None:
        """Handle a system status changed event sent ISY class."""
        # _LOGGER.info("System Status Changed: %s", SYSTEM_STATUS.get(event))

    try:
        if events:
            isy.websocket.start()
            node_changed_subscriber = isy.nodes.status_events.subscribe(
                node_changed_handler
            )
            system_status_subscriber = isy.status_events.subscribe(
                system_status_handler
            )
        
        with open("util.json", "r") as file:
            file_data = json.load(file)
        
        exhuast_fansObject = ExhuastFans(isy, file_data.get("exhuast_fan_node_names"))
        supply_fansObject = SupplyFans(isy, file_data.get("supply_fan_node_names"))

        while True:
            await asyncio.sleep(1)

            exhuast_fansObject.update()
            supply_fansObject.update()

            exhuast_fans = exhuast_fansObject.dict
            supply_fans = supply_fansObject.dict
            
            exhuast_cfm = await getExhuastCFM(exhuast_fans)
            supply_cfm = await getSupplyCFM(supply_fans)
            net_cfm = await balanceCFM(exhuast_fans, supply_fans, exhuast_cfm)

            for exhuast_fan in exhuast_fans:
                fan = exhuast_fans[exhuast_fan]
                print(fan)

            for supply_fan in supply_fans:
                fan = supply_fans[supply_fan]
                print(fan)
                    

            print("{}TOTAL EXHUAST CFM: {}{}".format(color.BOLD, exhuast_cfm, color.END))
            print("{}TOTAL SUPPLY CFM: {}{}".format(color.BOLD, supply_cfm, color.END))
            print("{}NET CFM: {}{}".format(color.BOLD, net_cfm, color.END))
            print(color.BOLD + time.ctime(time.time()) + color.END)
            print("-----------------------------------------")

              
               
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
        
        if type(fan.type) == int:
            ratio = 1/fan.type
            cfm += round(fan.cfm * fan.value * ratio)

    return cfm

async def getSupplyCFM(supply_fans):
    cfm = 0
    for supply_fan in supply_fans:
        fan = supply_fans[supply_fan]
        # print(fan)
        
        if fan.type == "bool":
            cfm += fan.value and fan.cfm
        
        if type(fan.type) == int:
            ratio = 1/fan.type
            cfm += round(fan.cfm * fan.value * ratio)
            
    return cfm

async def getFan(exhuast_fans, supply_fans, node_name):
    for fan in exhuast_fans:
        if fan == node_name:
            return exhuast_fans[fan]
    for fan in supply_fans:
        if fan == node_name:
            return supply_fans[fan]

def getSupplyFanISYNode(supply_fans, index):
    with open("util.json", "r") as file:
        file_data = json.load(file)
    node_name = file_data["supply_fan_node_names"][index]
    return supply_fans[node_name].node

async def turnOffSupplies(damper, fan_12_inch, fan_8_inch):
    await damper.node.turn_off()
    await fan_12_inch.node.turn_off()
    await fan_8_inch.node.turn_off()

async def balanceCFM(exhuast_fans, supply_fans, exhuast_cfm):
    FRESH_AIR = "n001_output_33"
    FRESH_AIR_FAN_12_INCH = "53 23 84 1"
    FRESH_AIR_FAN_8_INCH = "53 25 DA 1"

    damper = await getFan(exhuast_fans, supply_fans, FRESH_AIR)
    fan_12_inch = await getFan(exhuast_fans, supply_fans, FRESH_AIR_FAN_12_INCH)
    fan_8_inch = await getFan(exhuast_fans, supply_fans, FRESH_AIR_FAN_8_INCH)

    net_cfm = exhuast_cfm

    if net_cfm > 0:
        
        # if the damper is closed...
        if damper.value == 0:
            print("Opening the fresh air damper")
            await damper.node.turn_on()
            damper.time_off = time.time()
            
        net_cfm -= damper.cfm
        # if more supply is needed...
        print(net_cfm)
        if net_cfm > 0:
            # if the damper is fully open
            if time.time() - damper.time_off > 33:
                fan_percentage = min(1, net_cfm/fan_8_inch.cfm)
                cfm_of_fan = round(fan_percentage * fan_8_inch.cfm)
                print("Turning on fan for {} cfm".format(cfm_of_fan)) 
                on_level = round(fan_percentage * 255)
                fan_8_inch.value = on_level
                await fan_8_inch.node.turn_on(int(on_level))
                net_cfm -= cfm_of_fan
            else: 
                print("damper not open yet")
        else:
            # await turnOffSupplies(damper, fan_12_inch, fan_8_inch)
            await fan_8_inch.node.turn_off()
            await fan_12_inch.node.turn_off()
    else:
        await turnOffSupplies(damper, fan_12_inch, fan_8_inch)

    return net_cfm
        # damper_ISYnode = getSupplyFanISYNode(supply_fans, fresh_air)
        # fan_12_inch_ISYnode = getSupplyFanISYNode(supply_fans, fresh_air_fan_12_inch)
        # fan_8_inch_ISYnode = getSupplyFanISYNode(supply_fans, fresh_air_fan_8_inch)

        # if the damper is not open
        # if damper_ISYnode.value != 100:
        #     await damper_ISYnode.turn_on()
            

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

