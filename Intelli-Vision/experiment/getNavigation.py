import googlemaps
from datetime import datetime
import geocoder

gmaps = googlemaps.Client(key='AIzaSyCyyYEMD9w13RkHRfylHEjbzliCDfxoWuw')

g = geocoder.ip('me')
print(g.latlng)

# Geocoding an address
geocode_result = gmaps.geocode('Your Location')
print(f"Geo code result: {geocode_result}\ntype:{type(geocode_result)}\n")
# Look up an address with reverse geocoding
reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))

# Request directions via public transit
now = datetime.now()
directions_result = gmaps.directions(origin="S.R. Computer Training Centre",
                                     destination=
                                     'New Market / Hogg Market, Bertram Street, Esplanade, Dharmatala, Taltala, Kolkata, West Bengal',
                                     mode="transit",
                                     departure_time=now)
print(f"Direction result: {directions_result}")
# Validate an address with address validation
addressvalidation_result = gmaps.addressvalidation(['Hogg Market'],
                                                   regionCode='India',
                                                   locality='Kolkata',
                                                   enableUspsCass=True)
