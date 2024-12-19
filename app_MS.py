import streamlit as st
import requests
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
from branca.colormap import LinearColormap
from functools import partial
import os
from branca.element import Template, MacroElement

# Page Title
st.title("Risky Predictive Front")

# Function to retrieve the Ward using longitude and latitude
csv_path = os.path.join("raw_data", "ward_demographics_boundaries.csv")

# Simplify and Cache GeoDataFrame
@st.cache_data
def load_and_process_data(csv_path):
    ward_bound = pd.read_csv(csv_path)
    # Convert WKT strings to Shapely geometry objects
    ward_bound['the_geom'] = ward_bound['the_geom'].apply(wkt.loads)
    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(ward_bound, geometry='the_geom', crs="EPSG:4326")
    gdf['the_geom'] = gdf['the_geom'].simplify(tolerance=0.001, preserve_topology=True)
    return gdf

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

# Initialize session state for scrolling
if "scroll_to_graph" not in st.session_state:
    st.session_state.scroll_to_graph = False

# Function to get position as a tuple
@st.cache_data
def get_pos(lat, lng):
    return lat, lng

# Load data
gdf = load_and_process_data(csv_path)


# Define the function to create layers with a legend
def create_layer(gdf, column_name, layer_name, show_layer=False):
    colormap = LinearColormap(['green', 'yellow', 'red'],
                              vmin=0, vmax=100,
                          caption='Percentage (%)')  # Add caption for the legend

    def style_function(feature):
        value = feature['properties'][column_name]
        return {
            "fillColor": colormap(value),
            "color": "blue",
            "weight": 1.5,
            "fillOpacity": 0.6,
        }

    def highlight_function(feature):
        return {
            "fillColor": colormap(feature['properties'][column_name]),
            "color": "red",
            "weight": 2,
            "fillOpacity": 0.8,
        }

    # Add the GeoJSON layer to the map with tooltips and the defined style
    layer = folium.GeoJson(
        gdf,
        name=layer_name,
        tooltip=folium.features.GeoJsonTooltip(
            fields=["Ward", column_name],
            aliases=["Ward:", f"{layer_name} :"],
            localize=True
        ),
        style_function=style_function,
        highlight_function=highlight_function,
        show=show_layer,  # Show this layer only if `show_layer` is True
    ).add_to(m)

    # Add colormap (legend) to the map only when the layer is active
    if show_layer:
        colormap.add_to(m)

# Initialize map
chicago_coords = [41.8781, -87.6298]
m = folium.Map(location=chicago_coords, zoom_start=10)

# Define GeoDataFrame and column mappings

percentage_columns = [
    "Race-White_pct", "Race-Black_pct", "Race-Asian_pct",
    "Ethnicity-Hispanic_pct", "Income-24999_minus_pct",
    "Income-25000-49999_pct", "Income-50000-99999_pct",
    "Income-100000-149999_pct", "Income-150000_plus_pct"
]
layer_name_mapping = {
    "Race-White_pct": "White Population (%)",
    "Race-Black_pct": "Black Population (%)",
    "Race-Asian_pct": "Asian Population (%)",
    "Ethnicity-Hispanic_pct": "Hispanic Population (%)",
    "Income-24999_minus_pct": "Income <$25k (%)",
    "Income-25000-49999_pct": "Income $25k-$50k (%)",
    "Income-50000-99999_pct": "Income $50k-$100k (%)",
    "Income-100000-149999_pct": "Income $100k-$150k (%)",
    "Income-150000_plus_pct": "Income >$150k (%)"
}

# Add layers with readable names and a legend
for i, column in enumerate(percentage_columns):
    friendly_name = layer_name_mapping.get(column, column)
    create_layer(gdf, column, friendly_name, show_layer=(i == 0))

# Add LayerControl to switch layers
folium.LayerControl().add_to(m)

# Save the map
m.save("map_with_legend.html")

# Render the map using st_folium
map_output = st_folium(m, height=450, width=600)

# Handle map clicks
if map_output.get('last_clicked'):
    lat = map_output['last_clicked']['lat']
    lon = map_output['last_clicked']['lng']
    st.session_state.selected_coords = (lat, lon)

# Display clicked coordinates and ward details
if st.session_state.get('selected_coords'):
    selected_lat, selected_lon = st.session_state.selected_coords
    selected_ward = find_ward(selected_lat, selected_lon, gdf) # Replace with your `find_ward` function logic if needed
    #st.sidebar.write(f"**Latitude:** {selected_lat}")
    #st.sidebar.write(f"**Longitude:** {selected_lon}")
    #st.sidebar.write(f"**Ward:** {selected_ward if selected_ward else 'Not Found'}")
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


# API URL
api_url = "https://rpp2-589897242504.europe-west1.run.app/predict"

st.sidebar.markdown(
    """
    ---
    ### Make a Prediction
    Once all parameters are set, click the button below to retrieve an offense prediction from the API.
    """
)

# Call API and Get Prediction
if st.sidebar.button("Get Prediction"):
    if api_url and selected_ward and middle_time and selected_lat and selected_lon:
        # Prepare API request payload
        payload = {
            "ward": selected_ward,
            "date_of_occurrence": middle_time,
            "latitude": selected_lat,
            "longitude": selected_lon,
        }

        # Show payload in sidebar for user clarity
        st.sidebar.write(payload)

        try:
            # Make API request
            response = requests.post(api_url, json=payload)
            response_data = response.json()

            # Check if response status is 200 (success)
            if response.status_code == 200:
                # Scroll to the graph section
                st.markdown("<a name='graph_section'></a>", unsafe_allow_html=True)

                if st.session_state.get("scroll_to_graph", False):
                    # Reset the scroll flag
                    st.session_state.scroll_to_graph = False
                    # Scroll to the graph anchor
                    st.markdown(
                        """
                        <script>
                            document.querySelector("a[name='graph_section']").scrollIntoView({ behavior: 'smooth' });
                        </script>
                        """,
                        unsafe_allow_html=True,
                    )

                # Extract labels, probabilities, and counts from response
                labels = list(response_data["crime_types_probability"].keys())
                probabilities = [v * 100 for v in response_data["crime_types_probability"].values()]  # Convert to percentage
                counts = list(response_data["crime_types_count"].values())


                # Create a grouped bar chart for visualizing probabilities and counts
                fig = go.Figure()

                # Add probabilities bar
                fig.add_trace(go.Bar(
                    x=labels,
                    y=probabilities,
                    name="Likelihood of Offence Occurring (%)",
                    text=[f"{p:.1f}%" for p in probabilities],  # Show percentage text
                    textposition='outside',
                    marker_color='skyblue'
                ))

                # Add counts bar
                fig.add_trace(go.Bar(
                    x=labels,
                    y=counts,
                    name="Probable No. of Occurrences",
                    text=[f"{c}" for c in counts],  # Show count text
                    textposition='outside',
                    marker_color='orange'
                ))

                # Customize layout for a more informative and clean display
                fig.update_layout(
                    title="Crime Types: Likelihood and Counts",
                    xaxis_title="Crime Types",
                    yaxis_title="Values",
                    xaxis=dict(tickangle=-45),  # Rotate x-axis labels
                    barmode='group',  # Group bars side by side
                    template="plotly_white",  # Clean background style
                    legend=dict(title="Metrics"),
                    margin=dict(t=50, b=50),  # Add margin for better readability
                )

                # Display the chart
                st.plotly_chart(fig)

            else:
                st.sidebar.error("Failed to retrieve a valid prediction. Please check your inputs or API.")

        except Exception as e:
            st.sidebar.error(f"An error occurred: {e}")
    else:
        st.sidebar.warning("Please ensure all parameters are filled out correctly.")
