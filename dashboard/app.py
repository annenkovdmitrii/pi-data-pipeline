import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Environmental Monitor Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
st.markdown("""
    <style>
    .main-header {font-size:2.5rem; font-weight:bold; margin-bottom:1rem}
    .sub-header {font-size:1.5rem; font-weight:bold; margin-top:1.5rem}
    .metric-container {background-color:#f0f2f6; border-radius:5px; padding:1rem; margin:0.5rem}
    </style>
""", unsafe_allow_html=True)

# Database connection parameters
DB_HOST = "postgres"  # Docker service name
DB_PORT = "5432"
DB_NAME = "sensordata"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# Create SQLAlchemy engine
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Function to get database connection
def get_db_connection():
    try:
        return engine.connect()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Function to load sensor data
def load_sensor_data(time_range):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
        
    try:
        if time_range == "Last hour":
            time_filter = "timestamp > NOW() - INTERVAL '1 hour'"
        elif time_range == "Last 24 hours":
            time_filter = "timestamp > NOW() - INTERVAL '24 hours'"
        elif time_range == "Last 7 days":
            time_filter = "timestamp > NOW() - INTERVAL '7 days'"
        else:  # All data
            time_filter = "TRUE"
        
        query = f"""
        SELECT * FROM sensor_readings 
        WHERE {time_filter}
        ORDER BY timestamp DESC
        """
        
        with conn:
            df = pd.read_sql(text(query), conn)
        
        # Convert timestamp to datetime if not already
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        return df
    except Exception as e:
        st.error(f"Error loading sensor data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# Function to load weather API data
def load_weather_data(time_range):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
        
    try:
        if time_range == "Last hour":
            time_filter = "timestamp > NOW() - INTERVAL '1 hour'"
        elif time_range == "Last 24 hours":
            time_filter = "timestamp > NOW() - INTERVAL '24 hours'"
        elif time_range == "Last 7 days":
            time_filter = "timestamp > NOW() - INTERVAL '7 days'"
        else:  # All data
            time_filter = "TRUE"
        
        query = f"""
        SELECT * FROM weather_api_data 
        WHERE {time_filter}
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql(query, conn)
        
        # Convert timestamp to datetime if not already
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        return df
    except Exception as e:
        st.error(f"Error loading weather data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# Calculate statistics for sensor data
def calculate_stats(df):
    if df.empty:
        return {}
        
    stats = {
        "temp_current": df['temperature'].iloc[0],
        "temp_min": df['temperature'].min(),
        "temp_max": df['temperature'].max(),
        "temp_avg": df['temperature'].mean(),
        
        "humidity_current": df['humidity'].iloc[0],
        "humidity_min": df['humidity'].min(),
        "humidity_max": df['humidity'].max(),
        "humidity_avg": df['humidity'].mean(),
        
        "pressure_current": df['pressure'].iloc[0],
        "pressure_min": df['pressure'].min(),
        "pressure_max": df['pressure'].max(),
        "pressure_avg": df['pressure'].mean(),
        
        "reading_count": len(df),
        "first_reading": df['timestamp'].min(),
        "last_reading": df['timestamp'].max(),
    }
    return stats

# Calculate statistics for weather API data
def calculate_weather_stats(df):
    if df.empty:
        return {}
        
    stats = {
        "temp_current": df['temperature'].iloc[0],
        "temp_min": df['temperature'].min(),
        "temp_max": df['temperature'].max(),
        "temp_avg": df['temperature'].mean(),
        
        "humidity_current": df['humidity'].iloc[0],
        "humidity_min": df['humidity'].min(),
        "humidity_max": df['humidity'].max(),
        "humidity_avg": df['humidity'].mean(),
        
        "pressure_current": df['pressure'].iloc[0],
        "pressure_min": df['pressure'].min(),
        "pressure_max": df['pressure'].max(),
        "pressure_avg": df['pressure'].mean(),
        
        "wind_speed_current": df['wind_speed'].iloc[0],
        "wind_direction_current": df['wind_direction'].iloc[0],
        "condition_current": df['condition'].iloc[0],
        "location": df['location'].iloc[0],
        
        "reading_count": len(df),
        "first_reading": df['timestamp'].min(),
        "last_reading": df['timestamp'].max(),
    }
    
    # Add AQI statistics if available
    if 'aqi' in df.columns and not df['aqi'].isna().all():
        stats["aqi_current"] = df['aqi'].iloc[0] if not pd.isna(df['aqi'].iloc[0]) else None
        stats["aqi_min"] = df['aqi'].min() if not df['aqi'].isna().all() else None
        stats["aqi_max"] = df['aqi'].max() if not df['aqi'].isna().all() else None
        stats["aqi_avg"] = df['aqi'].mean() if not df['aqi'].isna().all() else None
    
    # Add US EPA AQI index if available
    if 'us_epa_index' in df.columns and not df['us_epa_index'].isna().all():
        stats["us_epa_index"] = df['us_epa_index'].iloc[0] if not pd.isna(df['us_epa_index'].iloc[0]) else None
    
    # Add individual pollutant data if available
    for pollutant in ['pm2_5', 'pm10', 'o3', 'no2', 'so2', 'co']:
        if pollutant in df.columns and not df[pollutant].isna().all():
            stats[f"{pollutant}_current"] = df[pollutant].iloc[0] if not pd.isna(df[pollutant].iloc[0]) else None
    
    return stats

# Function to create a time series chart
def create_time_series(df, y_column, title, y_label, color):
    if df.empty or y_column not in df.columns or df[y_column].isna().all():
        return go.Figure()
        
    # Filter out NaN values
    filtered_df = df.dropna(subset=[y_column])
    
    # If still empty after filtering, return empty figure
    if filtered_df.empty:
        return go.Figure()
        
    # Ensure data is sorted by timestamp
    filtered_df = filtered_df.sort_values('timestamp')
    
    # Create the figure
    fig = px.line(
        filtered_df, 
        x='timestamp', 
        y=y_column,
        title=title
    )
    
    # Update layout and styling
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=y_label,
        hovermode="x unified",
        height=300,
    )
    
    # Update line style
    fig.update_traces(line=dict(color=color, width=2))
    
    return fig

# Function to create comparison chart between sensor and weather API data
def create_comparison_chart(sensor_df, weather_df, y_column, title, y_label):
    if (sensor_df.empty or weather_df.empty or 
        y_column not in sensor_df.columns or 
        y_column not in weather_df.columns or
        sensor_df[y_column].isna().all() or 
        weather_df[y_column].isna().all()):
        return go.Figure()
        
    # Filter out NaN values
    sensor_filtered = sensor_df.dropna(subset=[y_column])
    weather_filtered = weather_df.dropna(subset=[y_column])
    
    # If either is empty after filtering, return empty figure
    if sensor_filtered.empty or weather_filtered.empty:
        return go.Figure()
        
    # Ensure data is sorted by timestamp
    sensor_filtered = sensor_filtered.sort_values('timestamp')
    weather_filtered = weather_filtered.sort_values('timestamp')
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add sensor data
    fig.add_trace(
        go.Scatter(
            x=sensor_filtered['timestamp'], 
            y=sensor_filtered[y_column],
            name='Sense HAT',
            line=dict(color='#FF4B4B', width=2)
        )
    )
    
    # Add weather API data
    fig.add_trace(
        go.Scatter(
            x=weather_filtered['timestamp'], 
            y=weather_filtered[y_column],
            name='Weather API',
            line=dict(color='#1E88E5', width=2, dash='dash')
        )
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title=y_label,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=300,
    )
    
    return fig

# Function to get AQI color and category based on US EPA Index
def get_aqi_info(us_epa_index):
    if us_epa_index is None:
        return "#CCCCCC", "Unknown"
    
    categories = {
        1: ("Good", "#00E400"),
        2: ("Moderate", "#FFFF00"),
        3: ("Unhealthy for Sensitive Groups", "#FF7E00"),
        4: ("Unhealthy", "#FF0000"),
        5: ("Very Unhealthy", "#99004C"),
        6: ("Hazardous", "#7E0023")
    }
    
    category, color = categories.get(us_epa_index, ("Unknown", "#CCCCCC"))
    return color, category

# Initialize session state for tracking refresh time
if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = datetime.now()

# Main dashboard
st.markdown('<div class="main-header">Environmental Monitoring Dashboard</div>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.title("Dashboard Controls")

# Time range selection
time_range = st.sidebar.selectbox(
    "Select Time Range",
    ["Last hour", "Last 24 hours", "Last 7 days", "All data"],
    index=1  # Default to last 24 hours
)

# Data source selection
data_source = st.sidebar.radio(
    "Data Source",
    ["Sense HAT Only", "Weather API Only", "Both (Comparison)"],
    index=2  # Default to comparison
)

# Auto-refresh option
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
if auto_refresh:
    st.sidebar.info("Dashboard will refresh every 30 seconds")
    refresh_interval = 30
else:
    refresh_interval = None

# Manual refresh button
if st.sidebar.button("Refresh Now"):
    st.session_state.last_refresh_time = datetime.now()
    st.rerun()

# If auto-refresh is enabled, add automatic rerun
if auto_refresh:
    st_autorefresh(interval=refresh_interval * 1000, key="data_refresh")
    st.session_state.last_refresh_time = datetime.now()

# Load the data based on selected source
sensor_data = pd.DataFrame()
weather_data = pd.DataFrame()

if data_source in ["Sense HAT Only", "Both (Comparison)"]:
    sensor_data = load_sensor_data(time_range)
    
if data_source in ["Weather API Only", "Both (Comparison)"]:
    weather_data = load_weather_data(time_range)

# Display error message if no data
if data_source == "Sense HAT Only" and sensor_data.empty:
    st.warning("No sensor data available for the selected time range. Make sure the sensor collector script is running.")
    st.stop()
elif data_source == "Weather API Only" and weather_data.empty:
    st.warning("No weather API data available for the selected time range. Make sure the weather API collector script is running.")
    st.stop()
elif data_source == "Both (Comparison)" and (sensor_data.empty and weather_data.empty):
    st.warning("No data available from either source for the selected time range.")
    st.stop()

# Calculate statistics based on selected source
sensor_stats = {}
weather_stats = {}

if not sensor_data.empty:
    sensor_stats = calculate_stats(sensor_data)
    
if not weather_data.empty:
    weather_stats = calculate_weather_stats(weather_data)

# Current readings section based on selected source
if data_source == "Sense HAT Only":
    st.markdown('<div class="sub-header">Current Sensor Readings</div>', unsafe_allow_html=True)
    
    # Current metrics displayed in three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="Temperature",
            value=f"{sensor_stats['temp_current']:.1f} °C",
            delta=f"{(sensor_stats['temp_current'] - sensor_stats['temp_avg']):.1f} °C from avg"
        )
        st.markdown(f"""
        <small>
        Min: {sensor_stats['temp_min']:.1f} °C | 
        Max: {sensor_stats['temp_max']:.1f} °C | 
        Avg: {sensor_stats['temp_avg']:.1f} °C
        </small>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="Humidity",
            value=f"{sensor_stats['humidity_current']:.1f} %",
            delta=f"{(sensor_stats['humidity_current'] - sensor_stats['humidity_avg']):.1f} % from avg"
        )
        st.markdown(f"""
        <small>
        Min: {sensor_stats['humidity_min']:.1f} % | 
        Max: {sensor_stats['humidity_max']:.1f} % | 
        Avg: {sensor_stats['humidity_avg']:.1f} %
        </small>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="Pressure",
            value=f"{sensor_stats['pressure_current']:.1f} hPa",
            delta=f"{(sensor_stats['pressure_current'] - sensor_stats['pressure_avg']):.1f} hPa from avg"
        )
        st.markdown(f"""
        <small>
        Min: {sensor_stats['pressure_min']:.1f} hPa | 
        Max: {sensor_stats['pressure_max']:.1f} hPa | 
        Avg: {sensor_stats['pressure_avg']:.1f} hPa
        </small>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif data_source == "Weather API Only":
    st.markdown('<div class="sub-header">Current Weather Conditions</div>', unsafe_allow_html=True)
    
    # Current metrics displayed in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label=f"Temperature ({weather_stats['location']})",
            value=f"{weather_stats['temp_current']:.1f} °C",
            delta=f"{(weather_stats['temp_current'] - weather_stats['temp_avg']):.1f} °C from avg"
        )
        st.markdown(f"""
        <small>
        Min: {weather_stats['temp_min']:.1f} °C | 
        Max: {weather_stats['temp_max']:.1f} °C | 
        Avg: {weather_stats['temp_avg']:.1f} °C
        </small>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="Humidity",
            value=f"{weather_stats['humidity_current']:.1f} %",
            delta=f"{(weather_stats['humidity_current'] - weather_stats['humidity_avg']):.1f} % from avg"
        )
        st.markdown(f"""
        <small>
        Min: {weather_stats['humidity_min']:.1f} % | 
        Max: {weather_stats['humidity_max']:.1f} % | 
        Avg: {weather_stats['humidity_avg']:.1f} %
        </small>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="Pressure",
            value=f"{weather_stats['pressure_current']:.1f} hPa",
            delta=f"{(weather_stats['pressure_current'] - weather_stats['pressure_avg']):.1f} hPa from avg"
        )
        st.markdown(f"""
        <small>
        Min: {weather_stats['pressure_min']:.1f} hPa | 
        Max: {weather_stats['pressure_max']:.1f} hPa | 
        Avg: {weather_stats['pressure_avg']:.1f} hPa
        </small>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            label="Wind",
            value=f"{weather_stats['wind_speed_current']:.1f} km/h",
            delta=f"{weather_stats['wind_direction_current']}"
        )
        st.markdown(f"""
        <small>
        Condition: {weather_stats['condition_current']}
        </small>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Add Air Quality section if data is available
    if 'aqi_current' in weather_stats and weather_stats['aqi_current'] is not None:
        st.markdown('<div class="sub-header">Air Quality</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            
            # Determine AQI quality category and color
            epa_index = weather_stats.get('us_epa_index')
            aqi_color, aqi_category = get_aqi_info(epa_index)
            
            st.metric(
                label="Air Quality Index",
                value=f"{weather_stats['aqi_current']:.1f}",
                delta=aqi_category
            )
            
            # Display individual pollutants if available
            pollutant_info = []
            for pollutant, label in [
                ('pm2_5_current', 'PM2.5'), 
                ('pm10_current', 'PM10'),
                ('o3_current', 'Ozone'),
                ('no2_current', 'NO₂'),
                ('so2_current', 'SO₂'),
                ('co_current', 'CO')
            ]:
                if pollutant in weather_stats and weather_stats[pollutant] is not None:
                    pollutant_info.append(f"{label}: {weather_stats[pollutant]:.2f}")
            
            if pollutant_info:
                st.markdown("<small>Pollutant levels:</small>", unsafe_allow_html=True)
                st.markdown(f"<small>{' | '.join(pollutant_info)}</small>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            if 'aqi_current' in weather_stats and 'aqi_min' in weather_stats and 'aqi_max' in weather_stats:
                # Create a gauge chart for AQI
                # Safely calculate max range for gauge and ensure we have a valid value
                max_range = 500  # Default max range
                aqi_value = 0  # Default AQI value
                
                if 'aqi_max' in weather_stats and weather_stats['aqi_max'] is not None:
                    max_range = max(500, float(weather_stats['aqi_max']) * 1.2)
                
                if 'aqi_current' in weather_stats and weather_stats['aqi_current'] is not None:
                    aqi_value = float(weather_stats['aqi_current'])
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=aqi_value,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Air Quality Index"},
                    gauge={
                        'axis': {'range': [None, max_range]},
                        'bar': {'color': aqi_color},
                        'steps': [
                            {'range': [0, 50], 'color': "#00E400"},
                            {'range': [51, 100], 'color': "#FFFF00"},
                            {'range': [101, 150], 'color': "#FF7E00"},
                            {'range': [151, 200], 'color': "#FF0000"},
                            {'range': [201, 300], 'color': "#99004C"},
                            {'range': [301, 500], 'color': "#7E0023"}
                        ],
                    }
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

else:  # Comparison mode
    st.markdown('<div class="sub-header">Environmental Conditions Comparison</div>', unsafe_allow_html=True)
    
    # Create comparison tabs
    tab1, tab2, tab3 = st.tabs(["Temperature", "Humidity", "Pressure"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            if not sensor_data.empty:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric(
                    label="Sense HAT Temperature",
                    value=f"{sensor_stats['temp_current']:.1f} °C"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
        with col2:
            if not weather_data.empty:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric(
                    label=f"Weather API Temperature ({weather_stats['location']})",
                    value=f"{weather_stats['temp_current']:.1f} °C"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
        # Display temperature difference if both sources have data
        if not sensor_data.empty and not weather_data.empty:
            temp_diff = sensor_stats['temp_current'] - weather_stats['temp_current']
            st.info(f"Temperature Difference: {abs(temp_diff):.1f} °C ({'+' if temp_diff > 0 else ''}{temp_diff:.1f} °C from Sense HAT to Weather API)")
            
            # Display comparison chart
            temp_comparison = create_comparison_chart(
                sensor_data, 
                weather_data, 
                'temperature', 
                'Temperature Comparison', 
                'Temperature (°C)'
            )
            st.plotly_chart(temp_comparison, use_container_width=True)
            
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            if not sensor_data.empty:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric(
                    label="Sense HAT Humidity",
                    value=f"{sensor_stats['humidity_current']:.1f} %"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
        with col2:
            if not weather_data.empty:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric(
                    label=f"Weather API Humidity ({weather_stats['location']})",
                    value=f"{weather_stats['humidity_current']:.1f} %"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
        # Display humidity difference if both sources have data
        if not sensor_data.empty and not weather_data.empty:
            humidity_diff = sensor_stats['humidity_current'] - weather_stats['humidity_current']
            st.info(f"Humidity Difference: {abs(humidity_diff):.1f} % ({'+' if humidity_diff > 0 else ''}{humidity_diff:.1f} % from Sense HAT to Weather API)")
            
            # Display comparison chart
            humidity_comparison = create_comparison_chart(
                sensor_data, 
                weather_data, 
                'humidity', 
                'Humidity Comparison', 
                'Humidity (%)'
            )
            st.plotly_chart(humidity_comparison, use_container_width=True)
            
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            if not sensor_data.empty:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric(
                    label="Sense HAT Pressure",
                    value=f"{sensor_stats['pressure_current']:.1f} hPa"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
        with col2:
            if not weather_data.empty:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric(
                    label=f"Weather API Pressure ({weather_stats['location']})",
                    value=f"{weather_stats['pressure_current']:.1f} hPa"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
        # Display pressure difference if both sources have data
        if not sensor_data.empty and not weather_data.empty:
            pressure_diff = sensor_stats['pressure_current'] - weather_stats['pressure_current']
            st.info(f"Pressure Difference: {abs(pressure_diff):.1f} hPa ({'+' if pressure_diff > 0 else ''}{pressure_diff:.1f} hPa from Sense HAT to Weather API)")
            
            # Display comparison chart
            pressure_comparison = create_comparison_chart(
                sensor_data, 
                weather_data, 
                'pressure', 
                'Pressure Comparison', 
                'Pressure (hPa)'
            )
            st.plotly_chart(pressure_comparison, use_container_width=True)

# Show additional weather information if Weather API data is available
if data_source in ["Weather API Only", "Both (Comparison)"] and not weather_data.empty:
    st.markdown('<div class="sub-header">Additional Weather Information</div>', unsafe_allow_html=True)
    
    # Set up columns for the additional data
    col1, col2 = st.columns(2)
    
    with col1:
        # Create wind speed chart
        wind_chart = create_time_series(
            weather_data, 
            'wind_speed', 
            'Wind Speed Over Time', 
            'Wind Speed (km/h)', 
            '#43A047'
        )
        st.plotly_chart(wind_chart, use_container_width=True)
        
    with col2:
        # Create a table for weather conditions
        conditions_df = weather_data[['timestamp', 'condition', 'wind_direction']].copy()
        conditions_df['timestamp'] = conditions_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        conditions_df = conditions_df.rename(columns={
            'timestamp': 'Time',
            'condition': 'Weather Condition',
            'wind_direction': 'Wind Direction'
        })
        st.dataframe(conditions_df.head(10), use_container_width=True)
    
    # AQI section (if data available)
    if 'aqi' in weather_data.columns and not weather_data['aqi'].isna().all():
        st.markdown('<div class="sub-header">Air Quality Information</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Create AQI chart
            aqi_chart = create_time_series(
                weather_data, 
                'aqi', 
                'Air Quality Index Over Time', 
                'AQI', 
                '#FF5722'
            )
            st.plotly_chart(aqi_chart, use_container_width=True)
            
        with col2:
            # Find the first available pollutant to display
            pollutant_data = None
            pollutant_label = None
            pollutant_color = None
            
            pollutant_options = [
                ('pm2_5', 'PM2.5 Concentration', 'PM2.5 (µg/m³)', '#9C27B0'),
                ('pm10', 'PM10 Concentration', 'PM10 (µg/m³)', '#3F51B5'),
                ('o3', 'Ozone Concentration', 'O₃ (µg/m³)', '#2196F3'),
                ('no2', 'Nitrogen Dioxide Concentration', 'NO₂ (µg/m³)', '#009688'),
                ('so2', 'Sulfur Dioxide Concentration', 'SO₂ (µg/m³)', '#FF9800'),
                ('co', 'Carbon Monoxide Concentration', 'CO (µg/m³)', '#795548')
            ]
            
            # Find the first pollutant with data for display
            for pollutant_id, title, label, color in pollutant_options:
                if pollutant_id in weather_data.columns and not weather_data[pollutant_id].isna().all():
                    pollutant_data = weather_data
                    pollutant_label = label
                    pollutant_color = color
                    
                    # Create chart for the first available pollutant
                    pollutant_chart = create_time_series(
                        pollutant_data, 
                        pollutant_id, 
                        title, 
                        label, 
                        pollutant_color
                    )
                    st.plotly_chart(pollutant_chart, use_container_width=True)
                    break
            
            # If no pollutant data available, show a message
            if pollutant_data is None:
                st.info("No detailed pollutant data available in the selected time range.")

# Add Raw Data Section
if st.checkbox("Show Raw Data"):
    st.markdown('<div class="sub-header">Raw Data Tables</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sensor Data", "Weather API Data"])
    
    with tab1:
        if not sensor_data.empty:
            # Format timestamp for display
            display_sensor_data = sensor_data.copy()
            display_sensor_data['timestamp'] = display_sensor_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(display_sensor_data, use_container_width=True)
        else:
            st.info("No sensor data available for the selected time range.")
    
    with tab2:
        if not weather_data.empty:
            # Format timestamp for display
            display_weather_data = weather_data.copy()
            display_weather_data['timestamp'] = display_weather_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(display_weather_data, use_container_width=True)
        else:
            st.info("No weather API data available for the selected time range.")

# System Information
st.markdown('<div class="sub-header">System Information</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown("**Data Collection Status**", unsafe_allow_html=True)
    
    # Check recent data collection
    recent_threshold = datetime.now() - timedelta(minutes=15)
    
    sensor_status = "✅ Active" if (not sensor_data.empty and 
                                    sensor_data['timestamp'].max() > recent_threshold) else "❌ Inactive"
    
    weather_status = "✅ Active" if (not weather_data.empty and 
                                     weather_data['timestamp'].max() > recent_threshold) else "❌ Inactive"
    
    st.markdown(f"""
    <small>
    Sense HAT Collector: {sensor_status}<br>
    Weather API Collector: {weather_status}<br>
    </small>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown("**Dashboard Information**", unsafe_allow_html=True)
    
    # Display last refresh time and data point counts
    st.markdown(f"""
    <small>
    Last refresh: {st.session_state.last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}<br>
    Sensor readings: {len(sensor_data) if not sensor_data.empty else 0} data points<br>
    Weather readings: {len(weather_data) if not weather_data.empty else 0} data points<br>
    </small>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="margin-top: 2rem; text-align: center; color: #888;">
<small>Environmental Monitoring Dashboard | Raspberry Pi Data Pipeline</small>
</div>
""", unsafe_allow_html=True)