-- Create table for sensor readings
CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    pressure FLOAT NOT NULL
);

-- Create index on timestamp for faster queries
CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_readings(timestamp);

-- Create table for weather API data
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
);

-- Create index on timestamp for weather API data
CREATE INDEX IF NOT EXISTS idx_timestamp_weather ON weather_api_data(timestamp);
