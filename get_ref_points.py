import json
import sys
import requests
import os
import time
from math import sqrt
from geopy.distance import distance as geopy_distance
from tqdm import tqdm

def get_distance(coord1, coord2):
    """Calculates the distance between two coordinates in meters using geocoding library"""
    res = geopy_distance(coord1, coord2)
    km = res.km
    return km * 1000  # Convert to meters

if __name__ == "__main__":
    #Put google api key in the first argument of the script or in the environment variable GOOGLE_API_KEY
    google_api_key = None
    if 'GOOGLE_API_KEY' in os.environ:
        google_api_key = os.environ['GOOGLE_API_KEY']
    if google_api_key in ['', None]:
        google_api_key = sys.argv[1]
    enderecos_reais = json.load(open('data/enderecos_brasil.json', 'r'))
    for endereco in tqdm(enderecos_reais):
        print(endereco)
        lat = endereco['Latitude']
        lon = endereco['Longitude']
        coords = [lat, lon]

        #Makes a request to google maps API to get closest reference point within 150 meters
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=150&key={google_api_key}"
        #Change the url to Remove 'political' localities from the api results
        #url += '&type=establishment|restaurant|cafe|bar|store|shopping_mall|gym|park|hospital|pharmacy|point_of_interest|school|university|library|cinema|museum|theater|tourist_attraction|landmark|reference_point'
        #url += '&keyword=reference|point|landmark|monument|tourist_attraction|museum|theater|cinema|library|university|school|college'
        #url += '&language=pt-BR'
        # print(url)
        response = requests.get(url)
        closest_places = []
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                for place in data['results']:
                    place_coords = [
                        place['geometry']['location']['lat'],
                        place['geometry']['location']['lng']
                    ]
                    distance = get_distance(coords, place_coords)
                    place['distance'] = distance
                data['results'].sort(key=lambda x: x['distance'])
                n = 3
                for place in data['results']:
                    print(place['name'], place['vicinity'], place['distance'], place['types'])
                    closest_places.append({
                        "name": place['name'],
                        "address": place['vicinity'],
                        "types": place['types'],
                        "distance": place['distance'],
                    })
                    n -= 1
                    if n <= 0:
                        break

                print(f"Closest reference points: {closest_places}")
            else:
                print("No nearby places found.")
                print(data)
        else:
            print(f"Error fetching data from Google Maps API: {response.status_code}")
        endereco['ref_points'] = closest_places
        json.dump(enderecos_reais, open('generated/enderecos_brasil_with_ref_points.json', 'w'), 
            indent=4, ensure_ascii=False)
        time.sleep(1)
    
    