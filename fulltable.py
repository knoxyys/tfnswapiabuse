# fully working
import tkinter as tk
from tkinter import ttk
import re
import requests
import json
import time
from gtfs_realtime_1007_extension import proto__1_pb2

# please dont put this on github again
api_key = 'put it here also'

headers = {
    "accept": "application/x-google-protobuf",
    "Authorization": f"apikey {api_key}"
}

vpResponse = requests.get('https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses', headers=headers)
vpList = []

# Fetch the fleet data from JSON file
def load_fleet_data(json_file):
    with open(json_file, "r") as f:
        return json.load(f)

# Normalize registration numbers (e.g., MOxxxx -> m/o xxxx)
def normalize_rego(rego):
    rego = rego.upper()
    match = re.match(r"MO(\d+)", rego)
    if match:
        return f"m/o {match.group(1)}"
    match = re.match(r"(\d+)MO", rego)
    if match:
        return f"{match.group(1)} MO"
    match = re.match(r"(\d+)ST", rego)
    if match:
        return f"{match.group(1)} ST"
    return rego

# Fetch vehicle positions and append to vpList
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
                    "route_id": bus.trip.route_id,
                    "licence_plate": bus.vehicle.license_plate,
                    "special_vehicle_attributes": bus.vehicle.Extensions[proto__1_pb2.tfnsw_vehicle_descriptor].special_vehicle_attributes,
                }
                vpList.append(bus_data)
    else:
        print(f"Request failed with status code {vpResponse.status_code}: {vpResponse.text}")

# Fetch data
vpFetch()

# Load fleet data (from the JSON file)
fleet_data = load_fleet_data("bus_fleet_data.json")

# Columns to display in the table
columns_to_display = ["route_id", "start_time", "fleet_no", "rego", "chassis", "body", "body_date", "seating", "livery", "depot", "operator", "body_no", "vin", "extra_info"]

# Function to create the table
def create_table(data, fleet_data, columns):
    sort_order = {col: True for col in columns}  # Store the sorting order (True for ascending, False for descending)

    # Function to sort data by column
    def sort_data(column, reverse=False):
        return sorted(data, key=lambda x: str(x.get(column, "")), reverse=reverse)

    # Function to handle column clicks for sorting
    def on_column_click(column):
        nonlocal sort_order
        sort_order[column] = not sort_order[column]  # Toggle sort order
        sorted_data = sort_data(column, reverse=not sort_order[column])
        update_table(sorted_data)

    # Function to update the table
    def update_table(data_to_display):
        search_term = search_var.get().lower()
        tree.delete(*tree.get_children())  # Clear the table

        for entry in data_to_display:
            rego_key = normalize_rego(entry["licence_plate"])
            fleet_info = fleet_data.get(rego_key, {})  # Get fleet data for matching rego

            # Merge the data, keeping original fields (route, time started) intact
            row_data = {
                **entry,  # Keep original data
                **fleet_info,  # Add fleet info from the JSON
            }

            # Prepare row values for the table
            row_values = [str(row_data.get(col, "")) for col in columns]
            
            # Apply search filter
            if any(search_term in value.lower() for value in row_values):
                tree.insert("", "end", values=row_values)

    root = tk.Tk()
    root.title("Opal Network Bus Tracker")
    root.state("zoomed")  # Full-screen mode

    top_frame = ttk.Frame(root)
    top_frame.pack(fill="x", padx=10, pady=5)

    search_var = tk.StringVar()
    search_var.trace_add("write", lambda *args: update_table(data))

    search_label = ttk.Label(top_frame, text="Search:")
    search_label.pack(side="left", padx=(0, 5))

    search_entry = ttk.Entry(top_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", fill="x", expand=True)
    
    text_label = ttk.Label(root, text="**probably not accurate\nTo search for regions:\nGreater Sydney: 2501 = Busways R1, 2502 = Transit Systems R2, 2503 = Transit Systems R3, 2504 = CDC R4, 2459 = Transit Systems R6, 2507 = Busways R7, 2508 = KD R8, 2509 = TDJH R9, 2510 = U-GO R10, 2514 = CDC R14\nOuter Sydney: 2447 = Rover Motors, 2448 = Hunter Valley North, 2449 = PSC, 2450 = Hunter Valley South, 2454 = Blue Mountains Transit, 2455, 2546, 2547 = Coastal Liner, 2548, 2606 = Busways OR6, 2607 = Red Bus OR7\nNewcastle: 3000 = Keolis Downer Newcastle\nReplacements: 7016? - 7073? = Train Replacement, 7083 = SW1 + SW3, 7084 = SW2", font=("Arial", 12))
    text_label.pack(pady=10)

    table_frame = ttk.Frame(root)
    table_frame.pack(expand=True, fill="both", padx=10, pady=10)

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: on_column_click(c))
        column_widths = {
            "route_id": 100,
            "start_time": 100,
            "fleet_no": 80,
            "rego": 80,
            "chassis": 150,
            "body": 180,
            "body_date": 100,
            "seating": 100,
            "livery": 150,
            "depot": 120,
            "operator": 150,
            "body_no": 120,
            "vin": 180,
            "extra_info": 500
        }

        for col in columns:
            width = column_widths.get(col, 150)  # Default to 150 if not specified
            tree.column(col, anchor="center", width=width, stretch=False)
        tree.heading(col, command=lambda col=col: on_column_click(col))

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

    update_table(data)
    root.mainloop()

# Create the table
create_table(vpList, fleet_data, columns_to_display)
