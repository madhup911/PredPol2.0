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
import plotly.graph_objects as go
from folium import LayerControl
from folium.plugins import Fullscreen
import branca.colormap as cm  # For generating color maps
import os

# Page Title
st.title("PredPol 2.0")

# Function to retrieve the Ward using longitude and latitude
csv_path = os.path.join("raw_data", "ward_demographics_boundaries.csv")
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
    PredPol 2.0 uses predictive analytics to forecast crimes in Chicago. Based on your inputs, it can predict:

    1.The top 5 most likely crime offenses
    2.The number of crime incidents predicted for the next 24 hours

    To enhance transparency, PredPol 2.0 also provides demographic details related to the prediction.
    Our model is trained on the 2023-2024 crime dataset from the Chicago Data Portal. We sourced demographic data from the American Community Survey, but this was not used in the training process. Please note: The crime dataset used is not free from bias, and the model has been trained on this data as-is. We understand there may be continued efforts to improve predictive policing technology to address these challenges. In any case, inherent biases in historical crime data remains a primary concern.
    This application is not affiliated with Geolitica (formerly PredPol, Inc.) and was developed as part of a research project during a Le Wagon Data Science & AI Bootcamp.
        ### How to Use
        1-Select a ward on the interactive map.
        2-Choose a date and time.
        3-Click “Get Prediction.”

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

# # Sample Chicago coordinates
# # chicago_coords = [41.8781, -87.6298]

# # Create the Folium map centered on Chicago
# m = folium.Map(location=chicago_coords, zoom_start=10)

# # Add ward boundaries to the map with custom highlighting
# def style_function(feature):
#     """Default style for all ward boundaries."""
#     return {
#         "fillColor": "#ADD8E6",  # Light blue fill
#         "color": "blue",         # Default boundary color
#         "weight": 1.5,           # Default line weight
#         "fillOpacity": 0.2,      # Slight transparency
#     }

# def highlight_function(feature):
#     """Style applied when a ward boundary is clicked or hovered."""
#     return {
#         "fillColor": "#FF0000",  # Red fill for the clicked ward
#         "color": "red",          # Red boundary color
#         "weight": 3,             # Thicker boundary line
#         "fillOpacity": 0.4,      # Slightly more opaque fill
#     }

# folium.GeoJson(
#     gdf,
#     name="Ward Boundaries",
#     tooltip=folium.features.GeoJsonTooltip(fields=["WARD"], aliases=["Ward:"]),
#     style_function=style_function,
#     highlight_function=highlight_function,  # Custom highlight on interaction
# ).add_to(m)

def create_layer(gdf, column_name, layer_name, show_layer=False):
    """
    Creates a Folium GeoJson layer with dynamic color styling based on column values.

    Parameters:
    - gdf: GeoDataFrame containing the data
    - column_name: Column name in the GeoDataFrame for styling
    - layer_name: Name of the layer to display on the map
    """
    # Create a color map ranging from green (low) to red (high)
    colormap = cm.LinearColormap(['green', 'yellow', 'red'],
                                 vmin=gdf[column_name].min(),
                                 vmax=gdf[column_name].max())

    # Define the style function using the colormap
    def style_function(feature):
        value = feature['properties'][column_name]
        return {
            "fillColor": colormap(value),
            "color": "blue",       # Boundary color
            "weight": 1.5,         # Line weight
            "fillOpacity": 0.6,    # Transparency
        }

    # Define the highlight function
    def highlight_function(feature):
        return {
            "fillColor": colormap(feature['properties'][column_name]),
            "color": "red",        # Highlight boundary color
            "weight": 2,           # Slightly thicker boundary
            "fillOpacity": 0.8,    # Less transparency when highlighted
        }

    # Add the GeoJson layer to the map
    folium.GeoJson(
        gdf,
        name=layer_name,
        tooltip=folium.features.GeoJsonTooltip(
            fields=["Ward"] + percentage_columns,  # Include all percentage columns in the tooltip
            aliases=["Ward:"] + [f"{col}:" for col in percentage_columns],  # Add column aliases
            localize=True
        ),
        style_function=style_function,
        highlight_function=highlight_function,
        show=show_layer,  # Control whether the layer is shown initially
    ).add_to(m)

# Create the map
chicago_coords = [41.8781, -87.6298]  # Latitude and Longitude of Chicago
m = folium.Map(location=chicago_coords, zoom_start=10)

# Add layers for each percentage column
percentage_columns = [
    "Race-White_pct",
    "Race-Black_pct",
    "Race-Asian_pct",
    "Ethnicity-Hispanic_pct",
    "Income-24999_minus_pct",
    "Income-25000-49999_pct",
    "Income-50000-99999_pct",
    "Income-100000-149999_pct",
    "Income-150000_plus_pct"
]

# Load only the first layer by default, others will be hidden initially
for i, column in enumerate(percentage_columns):
    create_layer(gdf, column, column, show_layer=(i == 0))  # Show only the first layer

# Add a layer control to switch between layers
folium.LayerControl().add_to(m)

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
