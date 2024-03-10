import time
import googlemaps  # pip install googlemaps
import sqlite3


def km_to_meters(km):
    try:
        return km * 1000
    except:
        return 0
    


# Function to create a SQLite table if it doesn't exist

def create_table(cursor):
    cursor.execute('''DROP TABLE IF EXISTS hospitales''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS hospitales (
                        place_id TEXT PRIMARY KEY,
                        name TEXT,
                        lat REAL,
                        lng REAL,
                        url TEXT,
                        rating REAL,
                        opening_hours TEXT,
                        reviews TEXT,
                        website TEXT,
                        distance TEXT,
                        wheelchair_accessible_entrance TEXT,
                        formatted_phone_number TEXT)''')

# Function to insert data into the SQLite table
def insert_data(cursor, hospital_list, user_location):
    for hospital in hospital_list:
        place_id = hospital['place_id']
        name = hospital.get('name', '')
        lat = hospital['geometry']['location']['lat']
        lng = hospital['geometry']['location']['lng']
        url = 'https://www.google.com/maps/place/?q=place_id:' + place_id
        
        # Fetch additional place details
        # Fetch additional place details including wheelchair_accessible_entrance
        place_details = map_client.place(place_id=place_id, fields=['rating', 'opening_hours', 'reviews', 'website', 'wheelchair_accessible_entrance', 'formatted_phone_number'])
        print(place_details)
        # opening_hours = place_details['result'].get('opening_hours', {}).get('weekday_text', 'N/A')
        # rating = place_details['result'].get('rating', 'N/A')

        # if rating == 'N/A':
        #         rating = -1  # Or any other default value you prefer

        # reviews_list = place_details['result'].get('reviews', [])  # Default to an empty list if not found
        # reviews_str = ', '.join([review['text'] for review in reviews_list]) 
        # website = place_details['result'].get('website', 'N/A')
        # wheelchair_accessible_entrance = place_details['result'].get('wheelchair_accessible_entrance', 'N/A')
        # formatted_phone_number = place_details['result'].get('formatted_phone_number', 'N/A')
        result = place_details.get('result')
        rating = result.get('rating', -1)
        print(rating)
        if 'opening_hours' in result and 'weekday_text' in result['opening_hours']:
            opening_hours = '; '.join(result['opening_hours']['weekday_text'])  # Use semicolon as a delimiter
        else:
            opening_hours = 'N/A'

        # Join the reviews array (text of each review) into a string using a delimiter
        reviews_str = '; '.join([review['text'] for review in result.get('reviews', [])])  # Use semicolon as a delimiter

        wheelchair_accessible_entrance = result.get('wheelchair_accessible_entrance', 'N/A')
        formatted_phone_number = result.get('formatted_phone_number', 'N/A')
        website = result.get('website', 'N/A')
        # opening_hours = result['opening_hours']['weekday_text']

        
        # Calculate distance from the user's location to the hospital
        distance_result = map_client.distance_matrix(origins=user_location,
                                                     destinations=f"{lat},{lng}",
                                                     mode="driving")
        # Extract distance text
        distance_text = distance_result['rows'][0]['elements'][0].get('distance', {}).get('text', 'N/A')
        
        cursor.execute('INSERT OR IGNORE INTO hospitales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
               (place_id, name, lat, lng, url, rating, opening_hours, reviews_str, website, distance_text, wheelchair_accessible_entrance, formatted_phone_number))



API_KEY = open('../api_key.txt').read()
map_client = googlemaps.Client(API_KEY)

user_location = (49.262408, -123.245214)

# address = '333 Market St, San Francisco, CA'
# geocode = map_client.geocode(address=address)
# (lat, lng) = map(geocode[0]['geometry']['location'].get, ('lat', 'lng'))

search_string = 'doctor'
distance = km_to_meters(10)
hospital_list = []

response = map_client.places_nearby(
    location=user_location,
    keyword=search_string,
    radius=distance
)   

hospital_list.extend(response.get('results'))
next_page_token = response.get('next_page_token')

while next_page_token:
    time.sleep(2)  # Ensure not to violate googlemaps API terms of service
    response = map_client.places_nearby(
        location=user_location,
        keyword=search_string,
        radius=distance,
        page_token=next_page_token
    )   
    hospital_list.extend(response.get('results'))
    next_page_token = response.get('next_page_token')

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('local_hospitales.db')
cursor = conn.cursor()

# Create table and insert data
create_table(cursor)
insert_data(cursor, hospital_list, user_location)

# Commit changes and close the connection to the database
conn.commit()
conn.close()


