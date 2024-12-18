import streamlit as st
import requests
import pydeck as pdk
from datetime import datetime
import  pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import plotly.express as px
import os

# Page Title
st.title("Risky Predictive Front")

# Function to retrieve the Ward using longitude and latitude
csv_path = os.path.join("raw_data", "WARDS.csv")
ward_bound = pd.read_csv(csv_path)

# Convert WKT strings to Shapely geometry objects
ward_bound['the_geom'] = ward_bound['the_geom'].apply(wkt.loads)

# Create a GeoDataFrame
gdf = gpd.GeoDataFrame(ward_bound, geometry='the_geom', crs="EPSG:4326")

# Function to find the ward for a given latitude and longitude
def find_ward(lat, lon, geodataframe):
    point = Point(lon, lat)  # Create a Point (longitude first)
    for _, row in geodataframe.iterrows():
        if row['the_geom'].contains(point):  # Check if the point is inside the polygon
            return row['WARD']
    return None  # Return None if no ward contains the point

# Introduction
st.markdown(
    """
    Welcome to the **Risky Predictive Front**! This app allows you to interact with a predictive model for predicting offenses.
    Simply provide the required parameters below, and you'll receive a prediction instantly.

    ### How It Works
    1. Select a ward from the interactive map.
    2. Specify the necessary details.
    3. We call the predictive API to estimate.
    4. View the prediction right here!

    Get Started! :)
    """
)

# Input Parameters
st.sidebar.header("Configure Input Parameters")


# Initialize session state for coordinates
if 'selected_coords' not in st.session_state:
    st.session_state.selected_coords = None

# Function to get position as a tuple
@st.cache_data
def get_pos(lat, lng):
    return lat, lng

# Sample Chicago coordinates
chicago_coords = [41.8781, -87.6298]

# Create the Folium map centered on Chicago
m = folium.Map(location=chicago_coords, zoom_start=10)

# Add ward boundaries to the map with custom highlighting
def style_function(feature):
    """Default style for all ward boundaries."""
    return {
        "fillColor": "#ADD8E6",  # Light blue fill
        "color": "blue",         # Default boundary color
        "weight": 1.5,           # Default line weight
        "fillOpacity": 0.2,      # Slight transparency
    }

def highlight_function(feature):
    """Style applied when a ward boundary is clicked or hovered."""
    return {
        "fillColor": "#FF0000",  # Red fill for the clicked ward
        "color": "red",          # Red boundary color
        "weight": 3,             # Thicker boundary line
        "fillOpacity": 0.4,      # Slightly more opaque fill
    }

folium.GeoJson(
    gdf,
    name="Ward Boundaries",
    tooltip=folium.features.GeoJsonTooltip(fields=["WARD"], aliases=["Ward:"]),
    style_function=style_function,
    highlight_function=highlight_function,  # Custom highlight on interaction
).add_to(m)

# Render the map using st_folium
map_output = st_folium(m, height=550, width=700)

# Function to get clicked latitude
def get_click_lat():
    return map_output['last_clicked']['lat']

# Function to get clicked longitude
def get_click_lng():
    return map_output['last_clicked']['lng']

# Handle map clicks
if map_output.get('last_clicked'):
    st.session_state.selected_coords = get_pos(get_click_lat(), get_click_lng())

# Display coordinates
if st.session_state.selected_coords:
    selected_coords = st.session_state.selected_coords
    selected_latitude = selected_coords[0]
    selected_longitude = selected_coords[1]
    selected_ward = find_ward(selected_latitude,selected_longitude,gdf)
    st.write(f"**Latitude:** {selected_latitude}")
    st.write(f"**Longitude:** {selected_longitude}")
    st.write(f"**Ward:** {selected_ward}")
else:
    st.write("Click on the map to select a location.")



# Function to return middle time for a range based on category
def get_middle_time_for_category(category, selected_date):
    time_ranges = {
        "Late Evening": (0, 6),     # Midnight (00:00) to 06:00
        "Early Morning": (6, 9),    # 06:00 to 09:00
        "Late Morning": (9, 12),    # 09:00 to 12:00
        "Early Noon": (12, 15),     # 12:00 to 15:00
        "Late Noon": (15, 18),      # 15:00 to 18:00
        "Early Evening": (18, 24)   # 18:00 to Midnight (24:00)
    }

    # Get the time range for the selected category
    if category in time_ranges:
        start_hour, end_hour = time_ranges[category]
        middle_hour = (start_hour + end_hour) / 2

        # Convert to a datetime object with selected date
        middle_time = datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=middle_hour)
        return middle_time.strftime("%Y-%m-%d %H:%M")  # Format as Date and Time string (24-hour format)

    return None

# Sidebar: Date picker
selected_date = st.sidebar.date_input("Select a Date", datetime.today())

# Sidebar: Dropdown for categories
categories = ["Late Evening", "Early Morning", "Late Morning", "Early Noon", "Late Noon", "Early Evening"]
selected_category = st.sidebar.selectbox("Select a Time Category", categories)

# Get and display the middle time
if selected_category:
    middle_time = get_middle_time_for_category(selected_category, selected_date)
    if middle_time:
        st.write(f"### Selected Category: **{selected_category}**")
        st.write(f"Time: **{middle_time}**")
    else:
        st.error("Invalid Category Selected!")

# Latitude and Longitude input
#latitude = st.sidebar.number_input("Latitude", format="%f")
#longitude = st.sidebar.number_input("Longitude", format="%f")


# Determine if the date is a weekend
# def is_weekend(date_obj):
#     return "Yes" if date_obj.weekday() >= 5 else "No"

# weekend = is_weekend(selected_date)

# API URL
api_url = st.text_input("API URL", "https://rpp-589897242504.europe-west1.run.app/predict")

st.markdown(
    """
    ---
    ### Make a Prediction
    Once all parameters are set, click the button below to retrieve an offense prediction from the API.
    """
)

# Save inputs when "Submit" button is clicked
if st.button("Get Prediction"):
    st.session_state["selected_ward"] = selected_ward
    st.session_state["middle_time"] = str(middle_time)
    st.session_state["selected_latitude"] = selected_latitude
    st.session_state["selected_longitude"] = selected_longitude
    st.session_state["api_url"] = api_url
    st.success("Inputs saved! Go to the Output Page to see predictions.")
