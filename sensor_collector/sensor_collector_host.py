import time
import psycopg2
from datetime import datetime
from sense_hat import SenseHat

# Initialize Sense HAT
sense = SenseHat()

# Database connection parameters - connect to the Docker container
DB_HOST = "postgres"  
DB_PORT = "5432"
DB_NAME = "sensordata"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

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

# Check if database table exists, create if it doesn't
def ensure_table_exists(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                temperature FLOAT NOT NULL,
                humidity FLOAT NOT NULL,
                pressure FLOAT NOT NULL
            )
        """)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Table creation error: {e}")

# Store sensor data in the database
def store_sensor_data(conn, temperature, humidity, pressure, timestamp):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_readings (timestamp, temperature, humidity, pressure) VALUES (%s, %s, %s, %s)",
            (timestamp, temperature, humidity, pressure)
        )
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Data insertion error: {e}")
        return False

# Main function to collect and store data
def main():
    print("Starting sensor data collection...")
    
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
            # Get current time
            now = datetime.now()
            
            # Read sensor data
            temperature = sense.get_temperature()
            humidity = sense.get_humidity()
            pressure = sense.get_pressure()
            
            # Round values to 2 decimal places for better readability
            temperature = round(temperature, 2)
            humidity = round(humidity, 2)
            pressure = round(pressure, 2)
            
            # Print to console
            print(f"Time: {now}")
            print(f"Temperature: {temperature}°C")
            print(f"Humidity: {humidity}%")
            print(f"Pressure: {pressure} millibars")
            print("-" * 40)
            
            # Store in database
            success = store_sensor_data(conn, temperature, humidity, pressure, now)
            if not success:
                # Reconnect to database if connection was lost
                conn = get_db_connection()
                if conn is not None:
                    ensure_table_exists(conn)
            
            # Wait before next reading (30 seconds)
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("Data collection stopped by user")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
