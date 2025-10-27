from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import requests
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)

# API Keys - Replace with your own keys
LOCATIONIQ_API_KEY = "pk.3a7b0d8cd86a661cb6fb6125f7c31483"
OPENROUTESERVICE_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjljNTZhMTIzMzk3ZjQ5NDM5N2ZjODBhZmQ4YjUzNDgzIiwiaCI6Im11cm11cjY0In0="

# Data files
ROUTES_DIR = "routes"
ACTIVE_BUSES_FILE = "active_buses.json"

# Create necessary directories
os.makedirs(ROUTES_DIR, exist_ok=True)

# Initialize active buses file
if not os.path.exists(ACTIVE_BUSES_FILE):
    with open(ACTIVE_BUSES_FILE, 'w') as f:
        json.dump({}, f)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/driver')
def driver():
    return render_template('driver.html')

@app.route('/passenger')
def passenger():
    return render_template('passenger.html')

@app.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    """Autocomplete for location search"""
    query = request.args.get('q', '')
    
    if len(query) < 3:
        return jsonify([])
    
    try:
        url = f"https://api.locationiq.com/v1/autocomplete.php"
        params = {
            'key': LOCATIONIQ_API_KEY,
            'q': query,
            'limit': 5,
            'format': 'json'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        suggestions = []
        for item in data:
            suggestions.append({
                'display_name': item.get('display_name', ''),
                'lat': float(item.get('lat', 0)),
                'lon': float(item.get('lon', 0))
            })
        
        return jsonify(suggestions)
    except Exception as e:
        print(f"Autocomplete error: {e}")
        return jsonify([])

@app.route('/api/create_route', methods=['POST'])
def create_route():
    """Create a new bus route"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        route_name = data.get('route_name', '').strip()
        stops = data.get('stops', [])
        
        print(f"Received route creation request: {route_name}, {len(stops)} stops")
        
        # Validate route name
        if not route_name:
            return jsonify({'success': False, 'error': 'Route name is required'}), 400
        
        # Validate stops
        if not stops or len(stops) < 2:
            return jsonify({'success': False, 'error': 'At least 2 stops are required'}), 400
        
        # Validate stop structure
        for i, stop in enumerate(stops):
            if not isinstance(stop, dict):
                return jsonify({'success': False, 'error': f'Stop {i+1} has invalid format'}), 400
            
            if not all(key in stop for key in ['name', 'lat', 'lon']):
                return jsonify({'success': False, 'error': f'Stop {i+1} missing required fields (name, lat, lon)'}), 400
            
            # Validate coordinates
            try:
                lat = float(stop['lat'])
                lon = float(stop['lon'])
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    return jsonify({'success': False, 'error': f'Stop {i+1} has invalid coordinates'}), 400
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': f'Stop {i+1} has invalid coordinate values'}), 400
        
        # Save route to file
        route_file = os.path.join(ROUTES_DIR, f"{route_name}.json")
        
        route_data = {
            'route_name': route_name,
            'stops': stops,
            'created_at': datetime.now().isoformat()
        }
        
        with open(route_file, 'w') as f:
            json.dump(route_data, f, indent=2)
        
        print(f"Route '{route_name}' saved successfully with {len(stops)} stops")
        
        return jsonify({
            'success': True,
            'route_name': route_name,
            'message': f'Route "{route_name}" saved successfully with {len(stops)} stops'
        }), 200
        
    except Exception as e:
        print(f"Error creating route: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_route_data', methods=['GET'])
def get_route_data():
    """Get route data by route name"""
    try:
        route_name = request.args.get('route_name', '').strip()
        
        if not route_name:
            return jsonify({'success': False, 'error': 'Route name required'}), 400
        
        route_file = os.path.join(ROUTES_DIR, f"{route_name}.json")
        
        if not os.path.exists(route_file):
            return jsonify({'success': False, 'error': 'Route not found'}), 404
        
        with open(route_file, 'r') as f:
            route_data = json.load(f)
        
        return jsonify(route_data), 200
        
    except Exception as e:
        print(f"Error getting route data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/list_routes', methods=['GET'])
def list_routes():
    """Get list of all saved routes"""
    try:
        routes = []
        
        if os.path.exists(ROUTES_DIR):
            for filename in os.listdir(ROUTES_DIR):
                if filename.endswith('.json'):
                    route_file = os.path.join(ROUTES_DIR, filename)
                    with open(route_file, 'r') as f:
                        route_data = json.load(f)
                        routes.append({
                            'route_name': route_data.get('route_name'),
                            'stops_count': len(route_data.get('stops', [])),
                            'created_at': route_data.get('created_at')
                        })
        
        return jsonify({'success': True, 'routes': routes}), 200
        
    except Exception as e:
        print(f"Error listing routes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update_location', methods=['POST'])
def update_location():
    """Update driver's live location"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        route_name = data.get('route_name')
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not all([route_name, lat is not None, lon is not None]):
            return jsonify({'success': False, 'error': 'Missing required fields: route_name, lat, lon'}), 400
        
        # Validate coordinates
        try:
            lat = float(lat)
            lon = float(lon)
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid coordinate values'}), 400
        
        # Load active buses
        with open(ACTIVE_BUSES_FILE, 'r') as f:
            active_buses = json.load(f)
        
        # Update bus location
        active_buses[route_name] = {
            'lat': lat,
            'lon': lon,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save updated data
        with open(ACTIVE_BUSES_FILE, 'w') as f:
            json.dump(active_buses, f, indent=2)
        
        print(f"Updated location for route '{route_name}': ({lat}, {lon})")
        
        # Check if bus reached final destination
        route_file = os.path.join(ROUTES_DIR, f"{route_name}.json")
        if os.path.exists(route_file):
            with open(route_file, 'r') as f:
                route_data = json.load(f)
                stops = route_data.get('stops', [])
                
                if stops:
                    final_stop = stops[-1]
                    distance = haversine_distance(lat, lon, final_stop['lat'], final_stop['lon'])
                    
                    if distance < 0.1:  # Within 100 meters
                        print(f"Bus on route '{route_name}' reached final destination")
                        return jsonify({'success': True, 'completed': True}), 200
        
        return jsonify({'success': True, 'completed': False}), 200
        
    except Exception as e:
        print(f"Error updating location: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop_broadcasting', methods=['POST'])
def stop_broadcasting():
    """Stop broadcasting driver location"""
    try:
        data = request.json
        route_name = data.get('route_name')
        
        if not route_name:
            return jsonify({'success': False, 'error': 'Route name required'}), 400
        
        # Load and update active buses
        with open(ACTIVE_BUSES_FILE, 'r') as f:
            active_buses = json.load(f)
        
        if route_name in active_buses:
            del active_buses[route_name]
            print(f"Stopped broadcasting for route '{route_name}'")
        
        with open(ACTIVE_BUSES_FILE, 'w') as f:
            json.dump(active_buses, f, indent=2)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error stopping broadcast: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/active_routes', methods=['GET'])
def active_routes():
    """Get list of active bus routes"""
    try:
        with open(ACTIVE_BUSES_FILE, 'r') as f:
            active_buses = json.load(f)
        
        routes = list(active_buses.keys())
        return jsonify({'success': True, 'routes': routes}), 200
        
    except Exception as e:
        print(f"Error getting active routes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bus_status', methods=['POST'])
def bus_status():
    """Get bus location and ETA for passenger"""
    try:
        data = request.json
        route_name = data.get('route_name')
        passenger_lat = data.get('lat')
        passenger_lon = data.get('lon')
        
        if not all([route_name, passenger_lat is not None, passenger_lon is not None]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get bus location
        with open(ACTIVE_BUSES_FILE, 'r') as f:
            active_buses = json.load(f)
        
        if route_name not in active_buses:
            return jsonify({'success': False, 'error': 'Bus not active'}), 404
        
        bus_location = active_buses[route_name]
        
        # Get route stops
        route_file = os.path.join(ROUTES_DIR, f"{route_name}.json")
        
        if not os.path.exists(route_file):
            return jsonify({'success': False, 'error': 'Route not found'}), 404
        
        with open(route_file, 'r') as f:
            route_data = json.load(f)
            stops = route_data.get('stops', [])
        
        # Find nearest stop to passenger
        nearest_stop = None
        min_distance = float('inf')
        
        for stop in stops:
            distance = haversine_distance(passenger_lat, passenger_lon, stop['lat'], stop['lon'])
            if distance < min_distance:
                min_distance = distance
                nearest_stop = stop
        
        # Calculate ETA using OpenRouteService
        eta_minutes = None
        try:
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {
                'Authorization': OPENROUTESERVICE_API_KEY,
                'Content-Type': 'application/json'
            }
            payload = {
                'coordinates': [[bus_location['lon'], bus_location['lat']], 
                              [nearest_stop['lon'], nearest_stop['lat']]]
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                duration_seconds = result['routes'][0]['summary']['duration']
                eta_minutes = round(duration_seconds / 60)
        except Exception as e:
            print(f"ETA calculation error: {e}")
            # Fallback: estimate based on distance (assuming 40 km/h average)
            distance_km = haversine_distance(
                bus_location['lat'], bus_location['lon'],
                nearest_stop['lat'], nearest_stop['lon']
            )
            eta_minutes = round(distance_km / 40 * 60)
        
        return jsonify({
            'success': True,
            'bus_location': bus_location,
            'nearest_stop': nearest_stop,
            'eta_minutes': eta_minutes,
            'route_stops': stops
        }), 200
        
    except Exception as e:
        print(f"Error getting bus status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)