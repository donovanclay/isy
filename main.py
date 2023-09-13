import asyncio
import json
import logging
import os
import time
from urllib.parse import urlparse

from dotenv import load_dotenv
from pyisy import ISY
from pyisy.connection import ISYConnectionError, ISYInvalidAuthError, get_new_client_session
from pyisy.constants import NODE_CHANGED_ACTIONS
from pyisy.logging import enable_logging
from pyisy.nodes import NodeChangedEvent

import humidity
from color import color
# local files
from fan import ExhaustFans, SupplyFans
import AQITracker

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

        # -----------------------------------------
        # CLAY HUANG CODE STARTS HERE
        # -----------------------------------------

        with open("util.json", "r") as file:
            file_data = json.load(file)

            exhaust_fans_object = ExhaustFans(isy, file_data.get("exhaust_fan_node_names"))
            supply_fans_object = SupplyFans(isy, file_data.get("supply_fan_node_names"))
            humidity_controller = humidity.Humidity(isy, file_data)
        # aqi_tracker = AQITracker.AQITracker()

        while True:
            # this is the period for the clock cycle of the program
            # without this the program would always be running at full speed
            await asyncio.sleep(1)

            # if aqi_tracker.aqi_acceptable():
            #     isy.nodes["Craw"]
            # isy.nodes["Double Bathroom"].aux_properties["CLIHUM"].value
            if int(isy.variables.get_by_name("IAQ_on_off").status) == 1:
                await humidity_controller.check_humidity()

            exhaust_fans_object.update()
            supply_fans_object.update()

            exhaust_fans = exhaust_fans_object.dict
            supply_fans = supply_fans_object.dict

            exhaust_cfm = await get_exhaust_cfm(exhaust_fans)
            supply_cfm = await get_supply_cfm(supply_fans)
            net_cfm = float('-inf')

            if int(isy.variables.get_by_name("IAQ_on_off").status) == 1:
                net_cfm = await balance_cfm(exhaust_fans, supply_fans, exhaust_cfm, supply_cfm)

            for exhaust_fan in exhaust_fans:
                fan = exhaust_fans[exhaust_fan]
                print(fan)

            for supply_fan in supply_fans:
                fan = supply_fans[supply_fan]
                print(fan)

            print("{}TOTAL EXHAUST CFM: {}{}".format(color.BOLD, exhaust_cfm, color.END))
            print("{}TOTAL SUPPLY CFM: {}{}".format(color.BOLD, supply_cfm, color.END))
            # print(isy.variables.get_by_name("IAQ_on_off").status)
            # print(int(isy.variables.get_by_name("IAQ_on_off").status) == 1)
            if int(isy.variables.get_by_name("IAQ_on_off").status) == 1:
                print("{}NET CFM: {}{}".format(color.BOLD, net_cfm, color.END))
            else:
                print("{}NOT BALANCING BECAUSE IAQ var = {} {}".format(color.BOLD,
                                                                       isy.variables.get_by_name("IAQ_on_off").status,
                                                                       color.END))
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


# This method returns the total exhaust cfm of all the fans
async def get_exhaust_cfm(exhaust_fans):
    cfm_ventahood = 0
    cfm = 0
    for exhaust_fan in exhaust_fans:
        fan = exhaust_fans[exhaust_fan]
        # print(fan)

        if fan.type == "bool":
            cfm += fan.value and fan.cfm
            # if fan.name.__contains__("Ventahood"):
            #     cfm_ventahood += fan.value and fan.cfm
            # else:
            #     cfm += fan.value and fan.cfm

        if type(fan.type) == int:
            ratio = 1 / fan.type
            cfm += round(fan.cfm * fan.value * ratio)
            # if fan.name.__contains__("Ventahood"):
            #     cfm_ventahood += round(fan.cfm * fan.value * ratio)
            # else:
            #     cfm += round(fan.cfm * fan.value * ratio)

    return cfm
    # return (cfm, cfm_ventahood)


async def get_supply_cfm(supply_fans):
    cfm = 0
    for supply_fan in supply_fans:
        fan = supply_fans[supply_fan]
        # print(fan)

        if fan.type == "bool":
            cfm += fan.value and fan.cfm

        if type(fan.type) == int:
            ratio = 1 / fan.type
            cfm += round(fan.cfm * fan.value * ratio)

    return cfm


async def get_fan(exhaust_fans, supply_fans, node_name):
    for fan in exhaust_fans:
        if fan == node_name:
            return exhaust_fans[fan]
    for fan in supply_fans:
        if fan == node_name:
            return supply_fans[fan]


async def turn_off_supplies(damper, fan_12_inch, fan_8_inch):
    await damper.node.turn_off()
    await fan_12_inch.node.turn_off()
    await fan_8_inch.node.turn_off()


# returns the CFM the supply fan is set to
async def turn_on_supply(fan, net_cfm):
    # print("fan status: " + str(fan.node.status))
    fan_percentage = min(1, net_cfm / fan.cfm)
    # print("fan percentage: " + str(fan_percentage))
    cfm_of_fan = round(fan_percentage * fan.cfm)
    print("Turning on fan for {} cfm".format(cfm_of_fan))
    on_level = round(fan_percentage * 255)
    fan.value = on_level
    if fan.node.status != int(on_level):
        await fan.node.turn_on(int(on_level))
    return cfm_of_fan


async def balance_cfm(exhaust_fans, supply_fans, exhaust_cfm, supply_cfm):
    DAMPER = "n001_output_33"
    FRESH_AIR_FAN_12_INCH = "53 23 84 1"
    FRESH_AIR_FAN_8_INCH = "53 25 DA 1"

    damper = await get_fan(exhaust_fans, supply_fans, DAMPER)
    fan_12_inch = await get_fan(exhaust_fans, supply_fans, FRESH_AIR_FAN_12_INCH)
    fan_8_inch = await get_fan(exhaust_fans, supply_fans, FRESH_AIR_FAN_8_INCH)

    fan_12_inch_reset = (0, False)

    net_cfm = exhaust_cfm

    if net_cfm > 0:

        print(exhaust_fans)
        if exhaust_fans["n001_zone_38"].value == 2:
            fan_12_inch_reset = (await turn_on_supply(fan_12_inch, net_cfm), True)
            net_cfm -= fan_12_inch_reset[0]

        # if the damper is closed...
        if damper.value == 0:
            print("Opening the fresh air damper")
            print("Status before: " + str(damper.node.status))
            await damper.node.turn_on()
            print("status after: " + str(damper.node.status))

            damper.time_off = time.time()
        net_cfm -= damper.cfm

        # if more supply is needed...
        if net_cfm > 0:

            # if the damper is fully open
            if time.time() - damper.time_off > 33:
                net_cfm -= await turn_on_supply(fan_8_inch, net_cfm)

            else:
                print("damper not open yet")

            # if more supply is needed...
            if net_cfm > 0:
                # if fan_12_inch_reset[1]:

                net_cfm -= await turn_on_supply(fan_12_inch, net_cfm)
            else:
                await fan_12_inch.node.turn_off()

        else:
            if fan_12_inch.node.status != 0:
                await fan_12_inch.node.turn_off()
            if fan_8_inch.node.status != 0:
                await fan_8_inch.node.turn_off()

    elif supply_cfm > 0:
        if damper.node.status != 0 or fan_12_inch.node.status != 0 or fan_8_inch.node.status != 0:
            await turn_off_supplies(damper, fan_12_inch, fan_8_inch)

    return net_cfm


if __name__ == "__main__":

    enable_logging(logging.DEBUG)

    _LOGGER.info(
        "ISY URL: %s, username: %s",
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
