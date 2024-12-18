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

# Page Title
st.title("Risky Predictive Front")

# Function to retrieve the Ward using longitude and latitude
ward_bound = pd.read_csv("raw_data/ward_demographics_boundaries.csv")

# Convert WKT strings to Shapely geometry objects
ward_bound['the_geom'] = ward_bound['the_geom'].apply(wkt.loads)

# Create a GeoDataFrame
gdf = gpd.GeoDataFrame(ward_bound, geometry='the_geom', crs="EPSG:4326")

# Function to find the ward for a given latitude and longitude
def find_ward(lat, lon, geodataframe):
    point = Point(lon, lat)  # Create a Point (longitude first)
    for _, row in geodataframe.iterrows():
        if row['the_geom'].contains(point):  # Check if the point is inside the polygon
            return row['Ward']
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

    Let's get started 🚔
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
# chicago_coords = [41.8781, -87.6298]

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

# # --- Helper Function for Color Styling ---
# def style_function(column_name):
#     """Generates a style function for choropleth-like layers."""
#     return lambda feature: {
#         "fillColor": "#ffeda0" if feature['properties'][column_name] is None else "#31a354",
#         "color": "black",
#         "weight": 0.5,
#         "fillOpacity": feature['properties'][column_name] / 100 if feature['properties'][column_name] else 0.3,
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
#     tooltip=folium.features.GeoJsonTooltip(fields=["Ward"], aliases=["Ward:"]),
#     style_function=lambda feature: {
#         "fillColor": "#ADD8E6",
#         "color": "blue",
#         "weight": 1.5,
#         "fillOpacity": 0.2,
#     },
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


# # --- Add Layers for Demographic and Income Data ---

#     # Layer for Race-White_pct
# folium.GeoJson(
#     gdf,
#     name="White Population %",
#     style_function=style_function("Race-White_pct"),
#     tooltip=folium.GeoJsonTooltip(fields=["Ward", "Race-White_pct"], aliases=["Ward:", "White Population %:"])
# ).add_to(m)

# # Layer for Race-Black_pct
# folium.GeoJson(
#     gdf,
#     name="Black Population %",
#     style_function=style_function("Race-Black_pct"),
#     tooltip=folium.GeoJsonTooltip(fields=["Ward", "Race-Black_pct"], aliases=["Ward:", "Black Population %:"])
# ).add_to(m)

# # Layer for Race-Asian_pct
# folium.GeoJson(
#     gdf,
#     name="Asian Population %",
#     style_function=style_function("Race-Asian_pct"),
#     tooltip=folium.GeoJsonTooltip(fields=["Ward", "Race-Asian_pct"], aliases=["Ward:", "Asian Population %:"])
# ).add_to(m)

# # Layer for Ethnicity-Hispanic_pct
# folium.GeoJson(
#     gdf,
#     name="Hispanic Ethnicity %",
#     style_function=style_function("Ethnicity-Hispanic_pct"),
#     tooltip=folium.GeoJsonTooltip(fields=["Ward", "Ethnicity-Hispanic_pct"], aliases=["Ward:", "Hispanic Ethnicity %:"])
# ).add_to(m)

# # Layers for Income Distribution
# income_columns = [
#     ("Income Below $25K", "Income-24999_minus_pct"),
#     ("Income $25K-$49K", "Income-25000-49999_pct"),
#     ("Income $50K-$99K", "Income-50000-99999_pct"),
#     ("Income $100K-$149K", "Income-100000-149999_pct"),
#     ("Income $150K Plus", "Income-150000_plus_pct")
# ]

# for layer_name, column_name in income_columns:
#     folium.GeoJson(
#         gdf,
#         name=layer_name,
#         style_function=style_function(column_name),
#         tooltip=folium.GeoJsonTooltip(fields=["Ward", column_name], aliases=["Ward:", f"{layer_name}:"])
#     ).add_to(m)

# # Add Layer Control and Fullscreen Option
# folium.LayerControl().add_to(m)
# Fullscreen().add_to(m)

# Render the map using st_folium
map_output = st_folium(m, height=450, width=600)

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
    st.sidebar.write(f"**Latitude:** {selected_latitude}")
    st.sidebar.write(f"**Longitude:** {selected_longitude}")
    st.sidebar.write(f"**Ward:** {selected_ward}")
else:
    st.sidebar.write("Click on the map to select a location.")



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
        pass
        #st.sidebar.write(f"### Selected Category: **{selected_category}**")
        #st.write(f"Time: **{middle_time}**")
    else:
        st.sidebar.error("Invalid Category Selected!")

# Latitude and Longitude input
#latitude = st.sidebar.number_input("Latitude", format="%f")
#longitude = st.sidebar.number_input("Longitude", format="%f")


# Determine if the date is a weekend
# def is_weekend(date_obj):
#     return "Yes" if date_obj.weekday() >= 5 else "No"

# weekend = is_weekend(selected_date)

# API URL
api_url = st.text_input("API URL", "https://rpp-589897242504.europe-west1.run.app/predict")

st.sidebar.markdown(
    """
    ---
    ### Make a Prediction
    Once all parameters are set, click the button below to retrieve an offense prediction from the API.
    """
)

# Call API and Get Prediction
if st.sidebar.button("Get Prediction"):
    if api_url and selected_ward and middle_time and selected_latitude and selected_longitude:
        # Prepare API request payload
        payload = {
            "ward": selected_ward,
            "date_of_occurrence": middle_time,
            "latitude": selected_latitude,
            "longitude": selected_longitude,
        }
        #st.write(payload)
        st.sidebar.write(payload)
        try:
            # Make API request
            response = requests.post(api_url, json=payload)
            response_data = response.json()

            # Display Prediction
            if response.status_code == 200:
                # Prepare data
                labels = list(response_data['Top 5 Crimes'].keys())
                values = list(response_data['Top 5 Crimes'].values())
              # Convert values to percentages
                percentages = [v * 100 for v in values]

                # Create a bar chart with Plotly
                fig = go.Figure()

                # Add bars
                fig.add_trace(go.Bar(
                    x=labels,
                    y=percentages,
                    text=[f"{p:.1f}%" for p in percentages],  # Display percentages on bars
                    textposition='outside',  # Position text outside the bars
                    marker_color='skyblue'
                ))

                # Customize layout
                fig.update_layout(
                    title="Top 5 Crimes as Percentage",
                    xaxis_title="Crimes",
                    yaxis_title="Percentage (%)",
                    xaxis=dict(tickangle=-45),  # Rotate x-axis labels
                    template="plotly_white"  # Clean white background style
                )

                # Display the chart in Streamlit
                st.sidebar.plotly_chart(fig)
            else:
                st.sidebar.error("Failed to retrieve a valid prediction. Please check your inputs or API.")
        except Exception as e:
            st.sidebar.error(f"An error occurred: {e}")
    else:
        st.sidebar.warning("Please ensure all parameters are filled out correctly.")
