import folium.plugins
import folium
import math
import webbrowser
import os
import json
from pyproj import Proj, transform
from pyproj import CRS, Transformer
import mgrs 

class ImprovedMGRSArrowTool:
    def __init__(self):
        self.arrows = []
        self.mgrs_converter = mgrs.MGRS() 

    def latlon_to_mgrs(self, lat, lon, precision=5):
        """Convert latitude/longitude to true MGRS/USNG coordinate string."""
        try:
            mgrs_coord = self.mgrs_converter.toMGRS(lat, lon, MGRSPrecision=precision)
            return mgrs_coord
        except Exception as e:
            return f"Error: {str(e)}"
    
    def create_interactive_map(self, center_lat=52.705681, center_lon= 16.396344, zoom=12):
        """Create an interactive map for arrow placement"""
        # Create a Folium map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, 
                      tiles='OpenStreetMap')
        
        draw = folium.plugins.Draw(
            export=True,
            position='topleft',
            draw_options={
                'polyline': True,
                'marker': True,
                'circlemarker': False,
                'rectangle': False,
                'circle': False,
                'polygon': False
            }
        )
        draw.add_to(m)
        
        # Add instructions
        folium.Marker(
            [center_lat, center_lon],
            popup="""
            <b>Instructions:</b><br>
            1. Click on the line tool (second icon)<br>
            2. Click on the map to place the start of the arrow<br>
            3. Click again to place the end of the arrow<br>
            4. Use the export button to save your arrows<br>
            5. Close the browser and return to Python to see coordinates
            """,
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
        
        # Add a custom JavaScript to handle the drawing events
        custom_js = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var map = document.querySelector('.folium-map')._leaflet_map;
            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);
            
            map.on(L.Draw.Event.CREATED, function (e) {
                var type = e.layerType;
                var layer = e.layer;
                
                if (type === 'polyline') {
                    var latlngs = layer.getLatLngs();
                    if (latlngs.length >= 2) {
                        // Get the first point (start of the arrow)
                        var start = latlngs[0];
                        var end = latlngs[latlngs.length - 1];
                        
                        // Calculate heading
                        var heading = calculateHeading(start, end);
                        
                        // Draw an arrow 
                        var arrowIcon = L.divIcon({
                            html: '<div style="transform: rotate(' + heading + 'deg); font-size: 24px;">➤</div>',
                            className: 'arrow-icon',
                            iconSize: [20, 20],
                            iconAnchor: [10, 10]
                        });
                        
                        L.marker([start.lat, start.lng], {icon: arrowIcon}).addTo(map);
                        
                        // Add information popup for the starting point
                        var info = "Position: " + start.lat.toFixed(6) + ", " + start.lng.toFixed(6) + 
                                   "<br>Heading: " + heading.toFixed(2) + "°" +
                                   "<br>(UTM/MGRS will be calculated in Python)";
                        
                        L.popup()
                            .setLatLng([start.lat, start.lng])
                            .setContent(info)
                            .openOn(map);
                    }
                }
                
                drawnItems.addLayer(layer);
            });
            
            function calculateHeading(start, end) {
                var lat1 = start.lat * Math.PI / 180;
                var lat2 = end.lat * Math.PI / 180;
                var lon1 = start.lng * Math.PI / 180;
                var lon2 = end.lng * Math.PI / 180;
                
                var y = Math.sin(lon2 - lon1) * Math.cos(lat2);
                var x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1);
                var heading = Math.atan2(y, x) * 180 / Math.PI;
                
                heading = (heading + 360) % 360;
                return heading;
            }
        });
        </script>
        <style>
        .arrow-icon {
            background: none;
            border: none;
        }
        </style>
        """
        
        m.get_root().html.add_child(folium.Element(custom_js))
        
        # Save the map to an HTML file
        map_file = "improved_arrow_map.html"
        m.save(map_file)
        
        # Open the map in the default web browser
        webbrowser.open('file://' + os.path.realpath(map_file))
        
        print(f"Interactive map opened in your browser. Place arrows and export when done.")
        print(f"After closing the browser, call the process_arrows() method with the exported GeoJSON.")
    
# Example usage
if __name__ == "__main__":
    tool = ImprovedMGRSArrowTool()
    
    # # Launch the interactive map
    print("\nLaunching interactive map...")
    tool.create_interactive_map()
