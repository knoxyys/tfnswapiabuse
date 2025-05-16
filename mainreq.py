# old table from before fleetlists integration

import tkinter as tk
from tkinter import ttk

import requests
import json
import time
from gtfs_realtime_1007_extension import proto__1_pb2

api_key = 'put it here too'

headers = {
    "accept": "application/x-google-protobuf",
    "Authorization": f"apikey {api_key}"
}

vpResponse = requests.get('https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses', headers=headers)
rtResponse = requests.get('https://api.transport.nsw.gov.au/v1/gtfs/realtime/buses', headers=headers)
vpList = []

# for stops (realtime)
def rtFetch():
    if rtResponse.status_code == 200:
        rtFeed = proto__1_pb2.FeedMessage()
        rtFeed.ParseFromString(rtResponse.content)
        print(f"rtResponse data fetched successfully")
                
        rtList = []
        for entity in rtFeed.entity:
            bus = entity.trip_update
            bus_data = {
                "time_retrieved": time.ctime(),
                "id": entity.id,
                
                "trip_id": bus.trip.trip_id,
                "start_time": bus.trip.start_time,
                "start_date": bus.trip.start_date,
                "schedule_relationship": bus.trip.schedule_relationship,
                "route_id": bus.trip.route_id,
                "stop_times": []
            }
            
            for stop in bus.stop_time_update:
                stop_data = {
                    "stop_sequence": stop.stop_sequence,
                    "stop_id": stop.stop_id,
                    "schedule_relationship": stop.schedule_relationship, # this might not be needed?
                        "arrival_delay": stop.arrival.delay,
                        "arrival_time": stop.arrival.time,
                        "departure_delay": stop.departure.delay,
                        "departure_time": stop.departure.time,
                }
                bus_data["stop_times"].append(stop_data)

            rtList.append(bus_data)
    
        with open("stop_data.json", "w") as json_file:
            json.dump(rtList, json_file, indent=2)
        print(f"JSON file updated successfully")
    
    else:
        print(f"Request failed with status code {vpResponse.status_code}: {vpResponse.text}")

# for positions
def vpFetch():
    if vpResponse.status_code == 200:
        vpFeed = proto__1_pb2.FeedMessage()
        vpFeed.ParseFromString(vpResponse.content)
        print(f"vpResponse data fetched successfully")

        for entity in vpFeed.entity:
            if entity.HasField("vehicle"):
                bus = entity.vehicle
                bus_data = {
                    "time_retrieved": time.ctime(),
                    "id": entity.id,
                    
                    "trip_id": bus.trip.trip_id,
                    "start_time": bus.trip.start_time,
                    "start_date": bus.trip.start_date,
                    "schedule_relationship": bus.trip.schedule_relationship,
                    "route_id": bus.trip.route_id,
                    
                    "latitude": bus.position.latitude,
                    "longitude": bus.position.longitude,
                    "bearing": bus.position.bearing,
                    "speed": bus.position.speed,
                    
                    "timestamp": bus.timestamp,
                    "congestion_level": bus.congestion_level,
                    
                    # "id_duplicate": bus.vehicle.id,
                    "label": bus.vehicle.label,
                    "licence_plate": bus.vehicle.license_plate,
                    
                    "occupancy_status": bus.occupancy_status,
                    
                    "air_conditioned": bus.vehicle.Extensions[proto__1_pb2.tfnsw_vehicle_descriptor].air_conditioned,
                    "wheelchair_accessible": bus.vehicle.Extensions[proto__1_pb2.tfnsw_vehicle_descriptor].wheelchair_accessible,
                    "vehicle_model": bus.vehicle.Extensions[proto__1_pb2.tfnsw_vehicle_descriptor].vehicle_model,
                    "special_vehicle_attributes": bus.vehicle.Extensions[proto__1_pb2.tfnsw_vehicle_descriptor].special_vehicle_attributes,
                }
                
                vpList.append(bus_data)
    
        with open("vehicle_pos.json", "w") as json_file:
            json.dump(vpList, json_file, indent=2)
        print(f"JSON file updated successfully")
    
    else:
        print(f"Request failed with status code {vpResponse.status_code}: {vpResponse.text}")

vpFetch()
# rtFetch() don't really need stops data yet



columns_to_display = ["route_id", "start_time", "vehicle_model", "licence_plate"]

def create_table(data, columns):
    def update_table(*args):
        """Filter table based on search input."""
        search_term = search_var.get().lower()
        tree.delete(*tree.get_children())  # Clear table

        for entry in data:
            row_values = [str(entry[col]) for col in columns]
            if any(search_term in value.lower() for value in row_values):
                tree.insert("", "end", values=row_values)

    def sort_column(col, reverse=False):
        """Sort table by column when header is clicked."""
        sorted_data = sorted(data, key=lambda x: str(x[col]).lower(), reverse=reverse)
        update_table_with_data(sorted_data)
        tree.heading(col, command=lambda: sort_column(col, not reverse))  # Toggle sort order

    def update_table_with_data(sorted_data):
        """Update table with sorted data."""
        tree.delete(*tree.get_children())
        for entry in sorted_data:
            row_values = [str(entry[col]) for col in columns]
            tree.insert("", "end", values=row_values)

    root = tk.Tk()
    root.title("Bus Information Table")
    root.state("zoomed")  # Set window to full screen

    top_frame = ttk.Frame(root)
    top_frame.pack(fill="x", padx=10, pady=5)

    search_var = tk.StringVar()
    search_var.trace_add("write", update_table)

    search_label = ttk.Label(top_frame, text="Search:")
    search_label.pack(side="left", padx=(0, 5))

    search_entry = ttk.Entry(top_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", fill="x", expand=True)

    table_frame = ttk.Frame(root)
    table_frame.pack(expand=True, fill="both", padx=10, pady=10)

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: sort_column(c))
        tree.column(col, anchor="center", width=150, stretch=True)  # Allow column resizing

    scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar_y.set)
    scrollbar_y.pack(side="right", fill="y")
    
    scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(xscroll=scrollbar_x.set)
    scrollbar_x.pack(side="bottom", fill="x")

    tree.pack(expand=True, fill="both")

    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="lightgray")
    style.configure("Treeview", font=("Arial", 10), rowheight=25)
    style.map("Treeview", background=[("selected", "#add8e6")])  # Light blue selection color
    
    update_table()
    root.mainloop()

create_table(vpList, columns_to_display)