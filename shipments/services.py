import requests
import logging

logger = logging.getLogger(__name__)


class RoutingService:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

    @classmethod
    def geocode_address(cls, address: str):
        """Converts text address into (latitude, longitude) using Nominatim OpenStreetMap."""
        headers = {'User-Agent': 'FleetOps-Platform/1.0'}
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        try:
            response = requests.get(cls.NOMINATIM_URL, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        except Exception as e:
            logger.error(f"Geocoding failed for {address}: {e}")
        return None, None

    @classmethod
    def get_route(cls, origin_lat, origin_lng, dest_lat, dest_lng):
        """Fetches route distance and GeoJSON geometry from OSRM."""
        coordinates = f"{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
        url = f"{cls.OSRM_URL}/{coordinates}?overview=full&geometries=geojson"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get('code') == 'Ok' and data.get('routes'):
                best_route = data['routes'][0]
                return {
                    'distance_km': round(best_route['distance'] / 1000, 2),
                    'duration_mins': round(best_route['duration'] / 60, 1),
                    'geometry': best_route['geometry']
                }
        except Exception as e:
            logger.error(f"Routing calculation failed: {e}")
        return None


class WeatherService:
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    WEATHER_DESCRIPTIONS = {
        0: "Clear Sky",
        1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Foggy", 48: "Depositing Rime Fog",
        51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
        61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
        80: "Slight Showers", 81: "Moderate Showers", 82: "Violent Showers",
        95: "Thunderstorm", 96: "Thunderstorm with Hail"
    }

    @classmethod
    def get_current_weather(cls, lat, lng):
        """
        Fetches current weather for coordinates.
        Returns: { 'temperature': float, 'windspeed': float, 'weather_code': int, 'condition': str, 'severity': int }
        """
        params = {
            'latitude': lat,
            'longitude': lng,
            'current_weather': 'true'
        }
        try:
            response = requests.get(cls.WEATHER_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json().get('current_weather', {})

            code = int(data.get('weathercode', 0))
            condition = cls.WEATHER_DESCRIPTIONS.get(code, "Clear Sky")

            # Severity score for ML: 0 = Clear, 1 = Fog, 2 = Rain, 3 = Thunderstorm
            severity = 0
            if code in [45, 48, 51, 53]:
                severity = 1
            elif code in [61, 63, 65, 80, 81]:
                severity = 2
            elif code in [82, 95, 96]:
                severity = 3

            return {
                'temperature': data.get('temperature', 28.0),
                'windspeed': data.get('windspeed', 10.0),
                'weather_code': code,
                'condition': condition,
                'severity': severity
            }
        except Exception as e:
            logger.error(f"Weather lookup failed: {e}")
            return {
                'temperature': 28.0,
                'windspeed': 10.0,
                'weather_code': 0,
                'condition': 'Clear Sky',
                'severity': 0
            }