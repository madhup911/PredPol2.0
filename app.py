import streamlit as st
import requests
import pydeck as pdk
from datetime import datetime
import  pandas as pd
# libraries for ward calculation
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
import folium
from streamlit_folium import st_folium


# Page Title
st.title("Risky Predictive Front")


# Function to retrieve the Ward using longitude and latitude
ward_bound = pd.read_csv("raw_data/WARDS.csv")

# Convert WKT strings to Shapely geometry objects
ward_bound['the_geom'] = ward_bound['the_geom'].apply(wkt.loads)

# Create a GeoDataFrame
gdf = gpd.GeoDataFrame(ward_bound, geometry='the_geom')

# Function to find the ward for a given latitude and longitude
def find_ward(lat, lon, geodataframe):
    point = Point(lon, lat)  # Create a Point (longitude first)
    for _, row in geodataframe.iterrows():
        if row['the_geom'].contains(point):  # Check if the point is inside the polygon
            return row['WARD']
    return None  # Return None if no ward contains the point
# Example usage
#new_lat, new_lon = 41.889, -87.627
#ward = find_ward(new_lat, new_lon, gdf)

# if ward:
#     print(f"The point ({new_lat}, {new_lon}) lies in Ward {ward}.")
# else:
#     print(f"The point ({new_lat}, {new_lon}) does not lie in any ward.")



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





# """ # Load ward data (GeoJSON for Chicago wards, replace with actual GeoJSON URL or file path)
# geojson_url = "https://data.cityofchicago.org/resource/igwz-8jzy.geojson"  # Updated GeoJSON URL for Chicago wards
# try:
#     response = requests.get(geojson_url)
#     response.raise_for_status()
#     wards_data = response.json()
#     if 'features' in wards_data:
#         wards = [
#             {
#                 "ward": feature['properties'].get('ward', 'Unknown Ward'),
#                 "centroid": feature['geometry']['coordinates'][0][0] if feature['geometry'] else [0, 0]
#             }
#             for feature in wards_data['features']
#         ]
#     else:
#         wards = []
#         st.error("GeoJSON does not contain 'features'. Check the data source.")
# except requests.RequestException as e:
#     wards = []
#     st.warning("Failed to load ward data. Interactive map will not display.")

# # Display interactive map
# if wards:
#     ward_data = [
#         {"ward": ward["ward"], "lon": centroid[0], "lat": centroid[1]}
#         for ward, centroid in [(w, w["centroid"]) for w in wards]
#     ]
#     ward_df = pd.DataFrame(ward_data)

#     st.pydeck_chart(pdk.Deck(
#         map_style="mapbox://styles/mapbox/light-v9",
#         initial_view_state=pdk.ViewState(
#             latitude=41.8781,  # Centered near Chicago
#             longitude=-87.6298,
#             zoom=10,
#             pitch=50,
#         ),
#         layers=[
#             pdk.Layer(
#                 "ScatterplotLayer",
#                 data=ward_df,
#                 get_position="[lon, lat]",
#                 get_color="[200, 30, 0, 160]",
#                 get_radius=200,
#                 pickable=True,
#             ),
#         ],
#     ))
#     selected_ward = st.sidebar.selectbox(
#         "Select Ward", [ward["ward"] for ward in wards]
#     )
# else:
#     selected_ward = st.sidebar.selectbox("Select Ward", options=["Ward data unavailable"])
# '''
# """

# Streamlit app
#st.title("Interactive Map of Chicago")
# st.write("Click on any point on the map to get the longitude and latitude of the point.")

# # Initialize the map centered on Chicago
# chicago_coords = [41.8781, -87.6298]  # Latitude and Longitude of Chicago
# m = folium.Map(location=chicago_coords, zoom_start=11)

# # Add instructions to the map
# folium.Marker(
#     chicago_coords,
#     popup="You can click anywhere on this map!",
#     tooltip="Chicago Center",
# ).add_to(m)

# folium.LatLngPopup().add_to(m)

# # Render the map using st_folium
# st.write("Map of Chicago:")
# output = st_folium(m, height=500, width=700)

# st.write("Debugging Output (Full Map Data):")
# st.json(output)  # Provides a cleaner JSON format for nested structures

# if output is not None:
#     if 'last_clicked' in output and output['last_clicked'] is not None:
#         st.write("You clicked on the point:")
#         st.write(f"**Latitude:** {output['last_clicked']['lat']}")
#         st.write(f"**Longitude:** {output['last_clicked']['lng']}")
#     else:
#         st.write("Click anywhere on the map to see the coordinates.")
# else:
#     st.write("Map output not available. Please refresh the page.")

# if 'clicked_coords' not in st.session_state:
#     st.session_state.clicked_coords = None

# if output and 'last_clicked' in output and output['last_clicked']:
#     st.session_state.clicked_coords = output['last_clicked']

# if st.session_state.clicked_coords:
#     st.write("You clicked on the point:")
#     st.write(f"**Latitude:** {st.session_state.clicked_coords['lat']}")
#     st.write(f"**Longitude:** {st.session_state.clicked_coords['lng']}")
# else:
#     st.write("Click anywhere on the map to see the coordinates.")


# Initialize session state for coordinates
if 'selected_coords' not in st.session_state:
    st.session_state.selected_coords = None

# Function to get position as a tuple
@st.cache_data
def get_pos(lat, lng):
    return lat, lng

# Create a map centered on Chicago

# Initialize session state for clicked ward and geometry
# if 'selected_ward' not in st.session_state:
#     st.session_state.selected_ward = None

# if 'selected_geometry' not in st.session_state:
#     st.session_state.selected_geometry = None




chicago_coords = [41.8781, -87.6298]  # Latitude and Longitude of Chicago
m = folium.Map(location=chicago_coords, zoom_start=10)
m.add_child(folium.LatLngPopup())  # Add click listener



# Add ward boundaries to the map
# Set the CRS for the GeoDataFrame (assuming data is in WGS 84)
gdf = gdf.set_crs(epsg=4326)

# Transform to a projected CRS for centroid calculation
#gdf_projected = gdf.to_crs(epsg=3857)

folium.GeoJson(
    gdf,  # GeoDataFrame
    name="Ward Boundaries",
    highlight_function=None,
    tooltip=folium.features.GeoJsonTooltip(fields=["WARD"], aliases=["Ward:"])
).add_to(m)

# Add labels for each ward (calculate centroids using projected CRS)
# for _, row in gdf_projected.iterrows():
#     if row['geometry'].is_valid:
#         # Calculate centroid of the geometry
#         centroid = row['geometry'].centroid
#         # Convert centroid back to WGS 84
#         centroid_wgs84 = gpd.GeoSeries([centroid], crs=3857).to_crs(epsg=4326).iloc[0]
#         folium.Marker(
#             location=[centroid_wgs84.y, centroid_wgs84.x],
#             popup=f"Ward: {row['WARD']}",
#             icon=folium.DivIcon(html=f"""<div style="font-size: 10px; color: black;">{row['WARD']}</div>""")
#         ).add_to(m)

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
    #pickup_latitude = st.number_input('Pickup Latitude', value=pickup_coords[0], format="%.6f")
    #pickup_longitude = st.number_input('Pickup Longitude', value=pickup_coords[1], format="%.6f")
    selected_latitude = selected_coords[0]
    selected_longitude = selected_coords[1]
    st.write(f"**Latitude:** {selected_latitude}")
    st.write(f"**Longitude:** {selected_longitude}")
    latitude = selected_latitude
    longitude = selected_longitude
    selected_ward = find_ward(selected_latitude, selected_longitude, gdf)
    #print ("selected ward is  ", selected_ward)
else:
    st.write("Click on the map to select a location.")

# Time category selection
time_category = st.sidebar.selectbox(
    "Time Category",
    ["Early Morning", "Late Morning", "Early Noon", "Late Noon", "Early Evening", "Late Evening"],
    index=0
)
# Date input
date = st.sidebar.date_input("Date")

# Latitude and Longitude input
#latitude = st.sidebar.number_input("Latitude", format="%f")
#longitude = st.sidebar.number_input("Longitude", format="%f")


# Determine if the date is a weekend
def is_weekend(date_obj):
    return "Yes" if date_obj.weekday() >= 5 else "No"

weekend = is_weekend(date)

# API URL
api_url = st.text_input("API URL", "https://rpp-589897242504.europe-west1.run.app/predict")

st.markdown(
    """
    ---
    ### Make a Prediction
    Once all parameters are set, click the button below to retrieve an offense prediction from the API.
    """
)

# Call API and Get Prediction
if st.button("Get Prediction"):
    if api_url and selected_ward and time_category and latitude and longitude:
        # Prepare API request payload
        payload = {
            "ward": selected_ward,
            "time_category": time_category,
            "date": date.strftime("%Y-%m-%d"),
            "weekend": weekend,
            "latitude": latitude,
            "longitude": longitude,
        }
        st.write(payload)
        try:
            # Make API request
            response = requests.post(api_url, json=payload)
            response_data = response.json()

            # Display Prediction
            if response.status_code == 200:
                prediction = response_data["offense_prediction"]
                st.success(f"The predicted offense likelihood is: {prediction:.2f}")
            else:
                st.error("Failed to retrieve a valid prediction. Please check your inputs or API.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please ensure all parameters are filled out correctly.")
