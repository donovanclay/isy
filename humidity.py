import json
import time


def get_hum(self):
    return self.aux_properties["CLIHUM"].value


def get_motion(self):
    match self.status:
        case 0:
            return False
        case 2:
            return True


class Room:
    # FIELDS
    # sens_hum: the humidity sensor
    # sens_motion: the motion sensor
    # fan: the fan that should turn on
    # hum: the humidity value that the fan should turn on at
    # hum_last_time: the last time the humidity was above "hum"
    # hum_t: the time the fan should be on for after humidity is too high
    # motion_power: the power the fan should be set to when motion is detected
    # motion_last_time: the last time motion was detected
    # motion_t: the time the fan should be on after motion detected

    def __init__(self, isy, sens_hum, sens_motion, fan, hum, hum_t, motion_power, motion_t):
        self.sens_hum = isy.nodes[sens_hum]
        self.sens_motion = isy.nodes[sens_motion]
        self.fan = isy.nodes[fan]
        self.hum = hum
        self.hum_last_time = 0
        self.hum_t = hum_t
        self.motion_power = motion_power
        self.motion_last_time = 0
        self.motion_t = motion_t


class Humidity:
    # FIELDS
    # rooms: a set of room objects
    def __init__(self, isy, json_dict):
        # def __init__(self, json_dict):
        rooms = set()

        for room in json_dict["honeywell_sens"]:
            rooms.add(Room(isy=isy,
                           sens_hum=room["sens_hum"],
                           sens_motion=room["sens_motion"],
                           fan=room["fan"],
                           hum=room["hum"],
                           hum_t=room["hum_t"],
                           motion_power=room["motion_power"],
                           motion_t=room["motion_t"]))
        self.rooms = rooms

    async def check_humidity(self):
        for room in self.rooms:

            if get_motion(room.sens_motion):
                room.motion_last_time = time.time()

            # if the humidity is too high
            if get_hum(room.sens_hum) >= room.hum:
                room.hum_last_time = time.time()

            if time.time() - room.hum_last_time < room.hum_t:
                if room.fan.status != 255:
                    await room.fan.turn_on(255)

            elif time.time() - room.motion_last_time < room.motion_t:
                if room.fan.status != int(room.motion_power):
                    await room.fan.turn_on(int(room.motion_power))

            else:
                if room.fan.status != 0:
                    await room.fan.turn_off()
