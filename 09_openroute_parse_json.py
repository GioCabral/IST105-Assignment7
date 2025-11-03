import os
import requests
from dotenv import load_dotenv

load_dotenv()


directions_api = "https://api.openrouteservice.org/v2/directions/driving-car"
geocode_api = "https://api.openrouteservice.org/geocode/search?"
key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImY2MTkxNTZhZDY4MjQ3YWJiMDk4Nzg4N2YxY2ZkNjE1IiwiaCI6Im11cm11cjY0In0="

def geocode_address(address):
    url = f"{geocode_api}api_key={key}&text={address}"
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
        return None
    data = r.json()
    feats = data.get("features", [])
    if not feats:
        print(f"No results for '{address}'")
        return None
    coords = feats[0]["geometry"]["coordinates"]
    lon, lat = coords
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        print(f"Invalid coordinates for '{address}'")
        return None
    return coords

def format_duration(sec):
    try:
        sec = int(round(sec))
    except:
        return "N/A"
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"

def get_route(orig_coords, dest_coords):
    body = {"coordinates": [orig_coords, dest_coords]}
    headers = {"Authorization": key, "Content-Type": "application/json"}
    r = requests.post(directions_api, headers=headers, json=body, timeout=30)
    return r

def estimate_fuel_liters(distance_km, l_per_100km=8.0):
    try:
        return round(distance_km * (l_per_100km / 100.0), 2)
    except:
        return None

while True:
    orig = input("Starting Location: ").strip()
    if orig.lower() in {"q", "quit", "exit"}:
        break
    dest = input("Destination: ").strip()
    if dest.lower() in {"q", "quit", "exit"}:
        break

    orig_coords = geocode_address(orig)
    dest_coords = geocode_address(dest)

    if not orig_coords or not dest_coords:
        print("Unable to geocode one or both addresses. Please try again.\n")
        continue

    try:
        resp = get_route(orig_coords, dest_coords)
        data = resp.json()
    except Exception as e:
        print(f"Request error: {e}\n")
        continue

    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {data}\n")
        continue

    routes = data.get("routes", [])
    if not routes:
        print("No routes found in the response.\n")
        continue

    route = routes[0]
    segs = route.get("segments", [])
    if not segs:
        print("No segments found in the route.\n")
        continue

    segment = segs[0]
    duration_sec = segment.get("duration", 0)
    distance_m = segment.get("distance", 0.0)
    distance_km = distance_m / 1000.0
    fuel_l = estimate_fuel_liters(distance_km)

    print("\nAPI Status: Successful route call.\n")
    print("=============================================")
    print(f"Directions from {orig} to {dest}")
    print(f"Trip Duration: {format_duration(duration_sec)}")
    print(f"Distance: {distance_km:.2f} km")
    if fuel_l is not None:
        print(f"Fuel Usage (est.): {fuel_l:.2f} L")
    print("=============================================")

    steps = segment.get("steps", [])
    if not steps:
        print("No step-by-step directions available.")
    else:
        for step in steps:
            instr = step.get("instruction", "N/A")
            sd = step.get("distance", 0.0)
            print(f"{instr} ({sd:.1f} m)")
    print("=============================================\n")
