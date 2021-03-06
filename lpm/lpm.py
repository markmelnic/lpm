import googlemaps, scalg
from geopy.distance import geodesic

from .utils import *
from .kmz_processor import KMZ


class LPM:
    def __init__(self, geo_key: str, weather_key: str) -> None:
        self.kmz = KMZ()
        self.weather_key = weather_key
        self.gmaps = googlemaps.Client(key=geo_key)

    def get_pollution(self, location: str) -> list:
        if type(location) == str:
            user_coords = self._user_location(location)
        elif type(location) == list or type(location) == tuple:
            user_coords = location

        item = self.kmz.coords_item(user_coords)
        edges, image = self.kmz.load_images(item[1], single=True, neighbours=True)
        closest_unique_spots = self._find_pollution_coords(user_coords, edges, image)

        for i, spot in enumerate(closest_unique_spots):
            elevation = self.gmaps.elevation(spot)[0]["elevation"]
            weather = get_coords_weather(spot)
            distance = geodesic(user_coords, spot).km
            closest_unique_spots[i] = [spot, distance, elevation] + weather

        if len(closest_unique_spots) == 1:
            return user_coords, closest_unique_spots[0]

        scored = scalg.score_columns(closest_unique_spots, [1, 2, 4], [0, 1, 0])
        return user_coords, sorted(scored, key=lambda x: x[-1])[-1]

    def _find_pollution_coords(
        self, user_coords: list, edges: list, image: bytes
    ) -> list:
        width, height = image.size
        pixelmap = image.load()

        wpx = int(height * (user_coords[1] - edges[3]) / (edges[2] - edges[3]))
        hpx = width - int(width * (user_coords[0] - edges[1]) / (edges[0] - edges[1]))

        ilev = 0
        cus = []  # closest_unique_spots
        indexed_colors = []
        for i in range(min(int(width/2), int(height/2))):
            ilev += 1
            layer = []

            # top row
            wpos = wpx - ilev
            for i in range(hpx - ilev, hpx + ilev):
                layer.append([wpos, i])

            # right column
            hpos = hpx + ilev
            for i in range(wpx - ilev, wpx + ilev):
                layer.append([i, hpos])

            # bottom row
            wpos = wpx + ilev
            for i in range(hpx - ilev + 1, hpx + ilev + 1):
                layer.append([wpos, i])

            # left column
            hpos = hpx - ilev
            for i in range(wpx - ilev + 1, wpx + ilev + 1):
                layer.append([i, hpos])

            for px in layer:
                try:
                    color = match_color(pixelmap[px[0], px[1]])
                except IndexError:
                    break
                if not color in indexed_colors and color in COLORS:
                    cus.append(self._matrix_geo_coords(width, height, edges, px))
                    indexed_colors.append(color)

            if len(cus) == len(COLORS):
                break

        return cus

    def _matrix_geo_coords(
        self, width: int, height: int, edges: list, matrix_coords: list
    ) -> tuple:
        return (
            edges[0] - ((edges[0] - edges[1]) / width * matrix_coords[1]),  # latitude
            edges[3] + ((edges[2] - edges[3]) / height * matrix_coords[0]),  # longitude
        )

    def _user_location(self, location: str) -> tuple:
        geocoded_location = self.gmaps.geocode(location)
        lat = geocoded_location[0]["geometry"]["location"]["lat"]
        lng = geocoded_location[0]["geometry"]["location"]["lng"]
        return (lat, lng)
