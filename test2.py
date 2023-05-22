import os
from dotenv import load_dotenv
import asyncio
import logging
import time
from urllib.parse import urlparse
import json
from fan import Fan, ExhuastFan, ExhuastFans, SupplyFan, SupplyFans
from color import color
import tkinter as tk
from tkinter import ttk
from typing import Tuple 

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

        window, exhuast_table, supply_table, total_cfm_label, supply_cfm_label, net_cfm_label = await makeGui()

        exhuast_fans = exhuast_fansObject.dict
        supply_fans = supply_fansObject.dict

        # for the gui
        await populateTables(exhuast_table, exhuast_fans, supply_table, supply_fans, window)

        while True:
            # this is the period for the clock cycle of the program
            # without this the program would always be running at full speed
            await asyncio.sleep(1)

            exhuast_fansObject.update()
            supply_fansObject.update()

            exhuast_fans = exhuast_fansObject.dict
            supply_fans = supply_fansObject.dict

            # gui thing
            await updateTables(exhuast_table, exhuast_fans, supply_table, supply_fans, window)

            # try:
            #     await updateTables(exhuast_table, exhuast_fans, supply_table, supply_fans, window)
            # except:
            #     pass

            # these "label" variables are for the gui 
            exhuast_cfm = await getExhuastCFM(exhuast_fans, total_cfm_label)
            supply_cfm = await getSupplyCFM(supply_fans, supply_cfm_label)
            net_cfm = await balanceCFM(exhuast_fans, supply_fans, exhuast_cfm, net_cfm_label)

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


# This method returns the total exhuast cfm of all the fans
async def getExhuastCFM(exhuast_fans, total_cfm_label) -> int:

    cfm = 0
    for exhuast_fan in exhuast_fans:
        fan = exhuast_fans[exhuast_fan]
        # print(fan)
        
        if fan.type == "bool":
            cfm += fan.value and fan.cfm
        
        if type(fan.type) == int:
            ratio = 1/fan.type
            cfm += round(fan.cfm * fan.value * ratio)

    try:
        total_cfm_label.config(text = "Total CFM: {}".format(cfm))
    except:
        pass
    return cfm

async def getSupplyCFM(supply_fans, supply_cfm_label):
    cfm = 0
    for supply_fan in supply_fans:
        fan = supply_fans[supply_fan]
        # print(fan)
        
        if fan.type == "bool":
            cfm += fan.value and fan.cfm
        
        if type(fan.type) == int:
            ratio = 1/fan.type
            cfm += round(fan.cfm * fan.value * ratio)
    try:       
        supply_cfm_label.config(text = "Supply CFM: {}".format(cfm))
    except:
        pass
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

async def balanceCFM(exhuast_fans, supply_fans, exhuast_cfm, net_cfm_label):
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
        print(net_cfm)

        # if more supply is needed...
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
            await fan_12_inch.node.turn_off()
            await fan_8_inch.node.turn_off()
    else:
        await turnOffSupplies(damper, fan_12_inch, fan_8_inch)

    try:
        net_cfm_label.config(text = "Net CFM: {}".format(net_cfm))
    except:
        pass

    return net_cfm
        # damper_ISYnode = getSupplyFanISYNode(supply_fans, fresh_air)
        # fan_12_inch_ISYnode = getSupplyFanISYNode(supply_fans, fresh_air_fan_12_inch)
        # fan_8_inch_ISYnode = getSupplyFanISYNode(supply_fans, fresh_air_fan_8_inch)

        # if the damper is not open
        # if damper_ISYnode.value != 100:
        #     await damper_ISYnode.turn_on()
            
async def makeGui():  
    # returns
    # Tuple[window, exhuast_table, supply_table, total_cfm_label, supply_cfm_label, net_cfm_label]

    WIDTH = 1200
    HEIGHT = 900
    COLUMNS = 4
    COLUMN_WIDTH = ((WIDTH//2)//COLUMNS) - 10

    window = tk.Tk()
    window.title("ClayHuang Indoor Air Quality")
    window.geometry("%dx%d" % (WIDTH, HEIGHT))
    window['bg'] = '#1f3456'

    total_cfm_label = tk.Label(window, text = "Total CFM: ", width=30, height=3, bg = "#64988d")
    total_cfm_label.place(relx=0.333, rely = 0.2, anchor=tk.CENTER)

    supply_cfm_label = tk.Label(window, text = "Supply CFM: ", width=30, height=3, bg = "#64988d")
    supply_cfm_label.place(relx=0.5, rely = 0.2, anchor=tk.CENTER)

    net_cfm_label = tk.Label(window, text = "Net CFM: ", width=30, height=3, bg = "#64988d")
    net_cfm_label.place(relx=0.666, rely = 0.2, anchor=tk.CENTER)

    exhuast_label = tk.Label(window, text = "Exhuasts", width=15, height=3, bg ="#1f3456", fg='#fff')
    exhuast_label.place(relx= 0.25, rely = 0.35, anchor=tk.CENTER)

    supply_label = tk.Label(window, text = "Supplies", width=15, height=3, bg ="#1f3456", fg='#fff')
    supply_label.place(relx= 0.75, rely = 0.35, anchor=tk.CENTER)

    frame1 = tk.Frame(window)
    # frame1.pack(ipadx=20, ipady=20, fill=tk.X, side=tk.LEFT)
    frame1.place(relx=0.25, rely=0.5, anchor=tk.CENTER)
    exhuast_table = ttk.Treeview(frame1)
    exhuast_table['columns'] = ('fan_name', 'fan_value', 'max_cfm', 'value_type')

    frame2 = tk.Frame(window)
    # frame2.pack(ipadx=20, ipady=20, fill=tk.X, side=tk.RIGHT)
    frame2.place(relx=0.75, rely=0.5, anchor=tk.CENTER)
    supply_table = ttk.Treeview(frame2)
    supply_table['columns'] = ('fan_name', 'fan_value', 'max_cfm', 'value_type')
    columns = [('fan_name', 'Fan Name'), ('fan_value', 'Value'), ('max_cfm', 'Max CFM'), ('value_type', 'Type')]

    exhuast_table.column("#0", width=0,  stretch=tk.NO)
    exhuast_table.heading("#0",text="",anchor=tk.CENTER)
    supply_table.column("#0", width=0,  stretch=tk.NO)
    supply_table.heading("#0",text="",anchor=tk.CENTER)
    for column in columns:
        exhuast_table.column(column[0], anchor=tk.CENTER, width=COLUMN_WIDTH)
        exhuast_table.heading(column[0],text=column[1],anchor=tk.CENTER)

        supply_table.column(column[0], anchor=tk.CENTER, width=COLUMN_WIDTH)
        supply_table.heading(column[0],text=column[1],anchor=tk.CENTER)

    return window, exhuast_table, supply_table, total_cfm_label, supply_cfm_label, net_cfm_label

async def populateTables(exhuast_table, exhuast_fans, supply_table, supply_fans, window):
    count = 0
    for fan in exhuast_fans:
        real_fan = exhuast_fans[fan]
        # my_table.insert(parent='',index='end',iid=0,text='', values = ('8 inch fan', '100', '418', '100'))
        exhuast_table.insert(parent='',index='end',iid=count,text='', values = (real_fan.name, real_fan.value, real_fan.cfm, real_fan.type))
        count+=1

    count = 0
    for fan in supply_fans:
        real_fan = supply_fans[fan]
        # my_table.insert(parent='',index='end',iid=0,text='', values = ('8 inch fan', '100', '418', '100'))
        supply_table.insert(parent='',index='end',iid=count,text='', values = (real_fan.name, real_fan.value, real_fan.cfm, real_fan.type))
        count+=1

    exhuast_table.pack()
    supply_table.pack()

    window.update()

async def updateTables(exhuast_table, exhuast_fans, supply_table, supply_fans, window):
    count = 0
    for fan in exhuast_fans:
        real_fan = exhuast_fans[fan]
        # my_table.insert(parent='',index='end',iid=0,text='', values = ('8 inch fan', '100', '418', '100'))
        exhuast_table.item(str(count), values = (real_fan.name, real_fan.value, real_fan.cfm, real_fan.type))
        count+=1

    count = 0
    for fan in supply_fans:
        real_fan = supply_fans[fan]
        # my_table.insert(parent='',index='end',iid=0,text='', values = ('8 inch fan', '100', '418', '100'))
        supply_table.item(str(count), values = (real_fan.name, real_fan.value, real_fan.cfm, real_fan.type))
        count+=1

    exhuast_table.pack()
    supply_table.pack()

    window.update()

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


