import folium.plugins
import webbrowser
import os
import json
import time
import math
import mgrs  # Import the MGRS conversion library
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileWatcher(FileSystemEventHandler):
    def __init__(self, tool, folder, filename):
        self.tool = tool
        self.folder = folder
        self.filename = filename

    def on_created(self, event):
        if event.src_path.endswith(self.filename):
            print(f"Detected new file: {event.src_path}")
            time.sleep(1)  # Allow time for file writing to complete
            self.tool.process_arrows(event.src_path)
            self.tool.display_coordinate_results()
            os._exit(0)  # Exit after processing

class ImprovedMGRSArrowTool:
    def __init__(self):
        self.arrows = []
        self.mgrs_converter = mgrs.MGRS()

    def latlon_to_mgrs(self, lat, lon, precision=5):
        try:
            return self.mgrs_converter.toMGRS(lat, lon, precision)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def create_interactive_map(self, center_lat=52.705681, center_lon=16.396344, zoom=12):
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles='OpenStreetMap')
        draw = folium.plugins.Draw(export=True, position='topleft', draw_options={'polyline': True, 'marker': True})
        draw.add_to(m)
        map_file = "improved_arrow_map.html"
        m.save(map_file)
        webbrowser.open('file://' + os.path.realpath(map_file))
        print("Interactive map opened. Place arrows and export when done.")
    
    def process_arrows(self, geojson_file):
        with open(geojson_file, 'r') as f:
            data = json.load(f)
        
        results = []
        for feature in data['features']:
            if feature['geometry']['type'] == 'LineString':
                coords = feature['geometry']['coordinates']
                if len(coords) >= 2:
                    start = coords[0]  # [lon, lat]
                    end = coords[-1]
                    heading = self.calculate_heading([start[1], start[0]], [end[1], end[0]])
                    mgrs_coord = self.latlon_to_mgrs(start[1], start[0])
                    mgrs_head = mgrs_coord[0:4]
                    x, y = mgrs_coord[5:10], mgrs_coord[10:16]
                    results.append({'lat': start[1], 'lon': start[0], 'mgrs_x': x, 'mgrs_y': y, 'mgrs_head': mgrs_head, 'heading_degrees': heading})
        
        self.arrows = results
        return results
    
    def calculate_heading(self, point1, point2):
        lat1, lon1 = map(math.radians, point1)
        lat2, lon2 = map(math.radians, point2)
        y = math.sin(lon2 - lon1) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
        return (math.degrees(math.atan2(y, x)) + 360) % 360
    
    def heading_to_quaternion(self, heading_degrees):
        heading_rad = math.radians(heading_degrees + 90)
        return [0.0, 0.0, math.cos(heading_rad / 2), math.sin(heading_rad / 2)]
    
    def display_coordinate_results(self):
        if not self.arrows:
            print("No arrows processed.")
            return
        for i, arrow in enumerate(self.arrows):
            quaternion = self.heading_to_quaternion(arrow['heading_degrees'])
            data = {"position_x": float(arrow['mgrs_x']), "position_y": float(arrow['mgrs_y']), "position_z": 0.0,
                    "orientation_x": quaternion[0], "orientation_y": quaternion[1], "orientation_z": quaternion[2], "orientation_w": quaternion[3]}
            with open(f"point{i+1}.yaml", 'w') as yaml_file:
                yaml.dump(data, yaml_file, default_flow_style=False)

if __name__ == "__main__":
    folder_to_watch = "."
    filename_to_watch = "data.geojson"
    tool = ImprovedMGRSArrowTool()
    tool.create_interactive_map()
    event_handler = FileWatcher(tool, folder_to_watch, filename_to_watch)
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=False)
    observer.start()
    print(f"Watching for file: {filename_to_watch} in {folder_to_watch}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
