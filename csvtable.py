import re
import requests
import json
import time
import csv
from gtfs_realtime_1007_extension import proto__1_pb2

# please dont put this on github again
api_key = 'put it here'

headers = {
    "accept": "application/x-google-protobuf",
    "Authorization": f"apikey {api_key}"
}

def normalize_rego(rego):
    match = re.match(r"MO(\d+)", rego)
    if match:
        return f"m/o {match.group(1)}"
    match = re.match(r"M0(\d+)", rego) # for u-go specimens
    if match:
        return f"m/o {match.group(1)}"
    match = re.match(r"(\d+)MO", rego)
    if match:
        return f"{match.group(1)} MO"
    match = re.match(r"(\d+)ST", rego)
    if match:
        return f"{match.group(1)} ST"
    match = re.match(r"TV(\d+)", rego) # for some nsbc replacements
    if match:
        return "TV " + rego.strip("TV")
    return "m/o " + rego # if rego not recognised, try shoving m/o in front of it (works with some sw bcis)

def get_rego_number(rego):
    match = re.search(r"(\d+)", rego)
    return int(match.group(1)) if match else float("inf")

def load_fleet_data(json_file):
    with open(json_file, "r") as f:
        return json.load(f)

def fetch_vehicle_positions():
    response = requests.get('https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses', headers=headers)
    if response.status_code != 200:
        print(f"Request failed: {response.status_code}")
        return []

    feed = proto__1_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    vp_list = []
    for entity in feed.entity:
        if entity.HasField("vehicle"):
            bus = entity.vehicle
            vp_list.append({
                "id": entity.id,
                "trip_id": bus.trip.trip_id,
                "start_time": bus.trip.start_time,
                "start_date": bus.trip.start_date,
                "route_id": bus.trip.route_id,
                "licence_plate": bus.vehicle.license_plate,
                "special_attrs": bus.vehicle.Extensions[proto__1_pb2.tfnsw_vehicle_descriptor].special_vehicle_attributes,
                "time_retrieved": time.ctime()
            })
    return vp_list

def main():
    print("Fetching data...")
    vp_list = fetch_vehicle_positions()
    fleet_data = load_fleet_data("bus_fleet_data.json") # do smth about this

    merged_list = []
    for bus in vp_list:
        rego_key = normalize_rego(bus["licence_plate"])
        fleet_info = fleet_data.get(rego_key, {})
        merged = {**bus, **fleet_info, "normalized_rego": rego_key}
        merged_list.append(merged)

    # Sort by rego
    sorted_list = sorted(merged_list, key=lambda x: get_rego_number(x["normalized_rego"]))

    # Fields to export
    columns = [
        "normalized_rego", "fleet_no", "route_id", "start_time", "trip_id",
        "start_date", "time_retrieved", "chassis", "body", "body_date", "seating",
        "livery", "depot", "operator", "body_no", "vin", "extra_info", "special_attrs"
    ]

    # Write to CSV
    with open("bus_data_output.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for row in sorted_list:
            writer.writerow({col: row.get(col, "") for col in columns})

    print(f"\n✅ Data exported to 'bus_data_output.csv'")

if __name__ == "__main__":
    main()
