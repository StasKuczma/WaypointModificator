import folium.plugins
import folium
import math
import webbrowser
import os
import json
from pyproj import Proj, transform
from pyproj import CRS, Transformer
import mgrs  # Import the MGRS conversion library
import yaml

class ImprovedMGRSArrowTool:
    def __init__(self):
        self.arrows = []
        self.mgrs_converter = mgrs.MGRS()  # Initialize MGRS conversion object

    def latlon_to_mgrs(self, lat, lon, precision=5):
        """Convert latitude/longitude to true MGRS/USNG coordinate string."""
        try:
            mgrs_coord = self.mgrs_converter.toMGRS(lat, lon, MGRSPrecision=precision)
            return mgrs_coord
        except Exception as e:
            return f"Error: {str(e)}"
    
    def process_arrows(self, geojson_data):
        """Process the exported GeoJSON to extract arrow starting points"""
        if isinstance(geojson_data, str):
            # If a string is provided, assume it's a file path
            try:
                with open(geojson_data, 'r') as f:
                    data = json.load(f)
            except:
                # If it's not a valid file path, assume it's the GeoJSON string
                data = json.loads(geojson_data)
        else:
            # If it's already a dictionary, use it directly
            data = geojson_data
        
        results = []
        
        for feature in data['features']:
            if feature['geometry']['type'] == 'LineString':
                coords = feature['geometry']['coordinates']
                if len(coords) >= 2:
                    # Get the first point (start of the arrow)
                    start = coords[0]  # [lon, lat]
                    end = coords[-1]   # [lon, lat]
                    
                    # Calculate heading
                    heading = self.calculate_heading([start[1], start[0]], [end[1], end[0]])
                    
                    # Convert to UTM/MGRS - for the starting point
                    mgrs_coord = self.latlon_to_mgrs(start[1], start[0])

                    mgrs_head= mgrs_coord[0:4]
                    x = mgrs_coord[5:10]
                    y = mgrs_coord[10:16]
                    
                    results.append({
                        'lat': start[1],
                        'lon': start[0],
                        'mgrs_x': x,
                        'mgrs_y': y,
                        'mgrs_head': mgrs_head,
                        'heading_degrees': heading
                    })
        
        self.arrows = results
        return results
    
    def calculate_heading(self, point1, point2):
        """Calculate heading between two points [lat, lon]"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Convert to radians
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)
        
        # Calculate heading
        y = math.sin(lon2 - lon1) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
        heading = math.atan2(y, x)
        
        # Convert to degrees
        heading = math.degrees(heading)
        heading = (heading + 360) % 360  # Normalize to 0-360
        
        return heading
    
    def heading_to_quaternion(self, heading_degrees):
        """Convert heading in degrees to quaternion.
        This creates a quaternion representing rotation around the Z axis."""
        # Convert heading to radians
        # heading_rad = math.radians(heading_degrees)
        heading_rad = math.radians(heading_degrees + 90)
        
        qx = 0.0
        qy = 0.0
        qz = math.cos(heading_rad / 2)
        qw = math.sin(heading_rad / 2)
        
        return [qx, qy, qz, qw]


    def save_to_yaml(arrow, filename):
        data = {
            'position_x': arrow['mgrs_x'],
            'position_y': arrow['mgrs_y'],
            'position_z': 0.0,
            'orientation_x': self.heading_to_quaternion(arrow['heading_degrees'])[0],
            'orientation_y': self.heading_to_quaternion(arrow['heading_degrees'])[1],
            'orientation_z': self.heading_to_quaternion(arrow['heading_degrees'])[2],
            'orientation_w': self.heading_to_quaternion(arrow['heading_degrees'])[3]
        }
        with open(filename, 'w') as yaml_file:
            yaml.dump(data, yaml_file, default_flow_style=False)
    
    def display_coordinate_results(self):
        """Display coordinates and heading for the starting points of arrows"""
        if not self.arrows:
            print("No arrows have been processed yet.")
            return
        
        print("\n===== Coordinates for Arrow Starting Points =====")
        for i, arrow in enumerate(self.arrows):
            print(f"\nArrow {i+1}:")
            # print(f"Latitude, Longitude: {arrow['lat']:.6f}, {arrow['lon']:.6f}")
            print(f"position_x: {arrow['mgrs_x']}")
            print(f"position_y: {arrow['mgrs_y']}")
            print(f"position_z: 0.0")
            print(f"orientation_x: {self.heading_to_quaternion(arrow['heading_degrees'])[0]}")
            print(f"orientation_y: {self.heading_to_quaternion(arrow['heading_degrees'])[1]}")
            print(f"orientation_z: {self.heading_to_quaternion(arrow['heading_degrees'])[2]}")
            print(f"orientation_w: {self.heading_to_quaternion(arrow['heading_degrees'])[3]}")

            data = {
            "position_x": float(arrow['mgrs_x']),
            "position_y": float(arrow['mgrs_y']),
            "position_z": 0.0,
            "orientation_x": self.heading_to_quaternion(arrow['heading_degrees'])[0],
            "orientation_y": self.heading_to_quaternion(arrow['heading_degrees'])[1],
            "orientation_z": self.heading_to_quaternion(arrow['heading_degrees'])[2],
            "orientation_w": self.heading_to_quaternion(arrow['heading_degrees'])[3],
            }
            with open("test.yaml", 'w') as yaml_file:
                yaml.dump(data, yaml_file, default_flow_style=False)

            # self.save_to_yaml(arrow, 'output.yaml')

    
if __name__ == "__main__":

    tool = ImprovedMGRSArrowTool()
    
    tool.process_arrows("data.geojson")


    tool.display_coordinate_results()
