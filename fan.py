import json
import time
from color import color


class Fan:

    # FIELDS
    # 
    # node: the isy node object
    # name: the english name of the node
    # value: the status of the isy.node
    # cfm: the cfm of the fan
    # type: # whether the fan status is binary or a scale
    # time_off: time since the fan was last turned off. 
    #           this is used for knowing when the freshair damper is open

    # this is the constructor method
    def __init__(self, isy, node_name: str):
        with open("util.json", "r") as file:
            file_data = json.load(file)

        self.node = isy.nodes[node_name]
        self.name = self.node.name
        self.value = self.node.status
        self.time_off = 0

    def update(self):
        old_value = self.value
        self.value = self.node.status

        # the fan has newly turned off
        if self.value == 0 and old_value != self.value:
            self.time_off = time.time()

    # this provides formatted console output
    def __str__(self):
        string = ""
        string += "Name: {}{}{}\n".format(color.UNDERLINE, self.name, color.END)
        string += "Value: {}\n".format(self.value)
        string += "CFM: {}\n".format(self.cfm)
        string += "Type: {}\n".format(self.type)
        return string


class ExhaustFan(Fan):

    # subclass of class fan

    # FIELDS
    # 
    # node: the isy node object
    # name: the english name of the node
    # value: the status of the isy.node
    # time_off: time since the fan was last turned off.
    # cfm: the cfm of the fan
    # type: # whether the fan status is binary or a scale
    #

    # this is the constructor method
    def __init__(self, isy, node_name: str):
        with open("util.json", "r") as file:
            file_data = json.load(file)
        super().__init__(isy, node_name)
        self.cfm = file_data["exhaust_fans"][node_name].get("cfm")
        self.type = file_data["exhaust_fans"][node_name].get("type")

    def __str__(self):
        string = ""
        string += "Name: {}{}{}\n".format(color.UNDERLINE, self.name, color.END)
        string += "Value: {}\n".format(self.value)
        string += "Time since last off: {}\n".format(self.time_off)
        string += "CFM: {}\n".format(self.cfm)
        string += "Type: {}\n".format(self.type)
        return string


class SupplyFan(Fan):

    # subclass of class fan

    # FIELDS
    # 
    # node: the isy node object
    # name: the english name of the node
    # value: the status of the isy.node
    # time_off: time since the turned on
    # cfm: the cfm of the fan
    # type: # whether the fan status is binary or a scale
    #

    # this is the constructor method
    def __init__(self, isy, node_name):
        with open("util.json", "r") as file:
            file_data = json.load(file)
        super().__init__(isy, node_name)
        self.cfm = file_data["supplies"][node_name].get("cfm")
        self.type = file_data["supplies"][node_name].get("type")


class FansDict:
    # FIELDS
    #
    # dict: a dictionary of the fans

    # updates the state of the fans
    def update(self):
        for fan in self.dict:
            self.dict[fan].update()


class ExhaustFans(FansDict):

    # this is the constructor method
    def __init__(self, isy, node_names):
        self.dict = {}
        for node_name in node_names:
            self.dict[node_name] = ExhaustFan(isy, node_name)


class SupplyFans(FansDict):

    # this is the constructor method
    def __init__(self, isy, supply_node_names):
        self.dict = {}
        for supply in supply_node_names:
            self.dict[supply] = SupplyFan(isy, supply)
