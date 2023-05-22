import json


# nodes = ["3F AF F7 1", "52 5B E6 6"]
# fans = []
# for node in nodes:
#     fans.append(isy.nodes[node])

with open("util.json", "r+") as file:
    file_data = json.load(file)
    for fan in file_data["supply_fan_names"]:
        file_data["supplies"].update({fan: {"name": "",
            "cfm": 418,
            "type": ""}})
        # print(fan)

    file.seek(0)
    json.dump(file_data, file, indent = 4)