import os
import time
import requests
import psycopg2
from datetime import datetime

# WeatherAPI.com configuration
API_KEY = os.environ.get("WEATHER_API_KEY", "your_api_key_here")
CITY = os.environ.get("WEATHER_CITY", "Manhattan,New York,USA")
BASE_URL = "http://api.weatherapi.com/v1/current.json"

# Database configuration
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "sensordata")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

# Connect to PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Ensure database table exists
def ensure_table_exists(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_api_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                temperature FLOAT NOT NULL,
                humidity FLOAT NOT NULL,
                pressure FLOAT NOT NULL,
                condition TEXT NOT NULL,
                wind_speed FLOAT NOT NULL,
                wind_direction TEXT NOT NULL,
                location TEXT NOT NULL,
                aqi FLOAT,
                pm2_5 FLOAT,
                pm10 FLOAT,
                o3 FLOAT,
                no2 FLOAT,
                so2 FLOAT,
                co FLOAT,
                us_epa_index INTEGER,
                gb_defra_index INTEGER
            )
        """)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Table creation error: {e}")

# Fetch weather data from API
def fetch_weather_data():
    try:
        params = {
            "key": API_KEY,
            "q": CITY,
            "aqi": "yes"  # Enable AQI data
        }
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Store weather data in database
def store_weather_data(conn, data):
    try:
        # Extract relevant data from API response
        current = data["current"]
        location = data["location"]["name"]
        
        timestamp = datetime.now()
        temperature = current["temp_c"]
        humidity = current["humidity"]
        pressure = current["pressure_mb"]
        condition = current["condition"]["text"]
        wind_speed = current["wind_kph"]
        wind_direction = current["wind_dir"]
        
        # Extract AQI data (if available)
        aqi = None
        pm2_5 = None
        pm10 = None
        o3 = None
        no2 = None
        so2 = None
        co = None
        us_epa_index = None
        gb_defra_index = None
        
        if "air_quality" in current:
            air_quality = current["air_quality"]
            # Some fields might be None if not available
            pm2_5 = air_quality.get("pm2_5")
            pm10 = air_quality.get("pm10")
            o3 = air_quality.get("o3")
            no2 = air_quality.get("no2")
            so2 = air_quality.get("so2")
            co = air_quality.get("co")
            us_epa_index = air_quality.get("us-epa-index")
            gb_defra_index = air_quality.get("gb-defra-index")
            
            # Calculate an average AQI (simplified)
            valid_values = [v for v in [pm2_5, pm10, o3, no2, so2, co] if v is not None]
            if valid_values:
                aqi = sum(valid_values) / len(valid_values)
        
        # Insert data into database
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO weather_api_data 
            (timestamp, temperature, humidity, pressure, condition, wind_speed, wind_direction, location,
             aqi, pm2_5, pm10, o3, no2, so2, co, us_epa_index, gb_defra_index)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (timestamp, temperature, humidity, pressure, condition, wind_speed, wind_direction, location,
             aqi, pm2_5, pm10, o3, no2, so2, co, us_epa_index, gb_defra_index)
        )
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Data insertion error: {e}")
        return False

# Main function
def main():
    print("Starting weather data collection...")
    
    # Wait for database to be ready
    conn = None
    while conn is None:
        print("Attempting to connect to database...")
        conn = get_db_connection()
        if conn is None:
            print("Database not available yet, waiting 5 seconds...")
            time.sleep(5)
    
    print("Connected to database successfully")
    ensure_table_exists(conn)
    
    # Main collection loop
    try:
        while True:
            print(f"Fetching weather data for {CITY}...")
            weather_data = fetch_weather_data()
            
            if weather_data:
                print("Weather data received:")
                print(f"Temperature: {weather_data['current']['temp_c']}°C")
                print(f"Humidity: {weather_data['current']['humidity']}%")
                print(f"Pressure: {weather_data['current']['pressure_mb']} mb")
                print(f"Condition: {weather_data['current']['condition']['text']}")
                
                if 'air_quality' in weather_data['current']:
                    print("Air Quality Data:")
                    aq = weather_data['current']['air_quality']
                    for key, value in aq.items():
                        if value is not None:
                            print(f"  {key}: {value}")
                
                success = store_weather_data(conn, weather_data)
                if success:
                    print("Weather data stored successfully")
                else:
                    print("Failed to store weather data")
                    # Reconnect to database if needed
                    conn = get_db_connection()
                    if conn is not None:
                        ensure_table_exists(conn)
            else:
                print("Failed to fetch weather data")
            
            # Wait before next API call (5 minutes to respect API limits)
            print("Waiting 5 minutes before next update...")
            time.sleep(300)  # 5 minutes
            
    except KeyboardInterrupt:
        print("Weather data collection stopped by user")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
