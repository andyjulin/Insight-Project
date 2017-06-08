import googlemaps
from datetime import datetime
from bs4 import BeautifulSoup

gmaps = googlemaps.Client(key='AIzaSyAm2m8M3Lfsqn_f_QwK_7cybr8ErEhzz-Y')


def get_direction_list(start_loc, end_loc, departure = None):
    if not departure:
        departure = datetime.now()

    directions_result = gmaps.directions(place_start, place_end, \
            mode="driving", departure_time=departure)

    data = directions_result[0]['legs'][0]['steps']

    dirs = [(data[d]['html_instructions'], data[d]['duration']['value']) \
            for d in range(len(data))]

    return dirs
