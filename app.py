import streamlit as st
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from folium import LayerControl
import branca.colormap as cm
import os

# Page Title
st.title("PredPol 2.0")

# INTRODUCTION
st.markdown(
    """
    ## PredPol 2.0: Crime Predictions
    Predict top crimes and incidents in Chicago using 2023-2024 data.
    **Note:** May reflect biases in historical data.

    ### How to Use
    1. Select a ward.
    2. Pick a date and time.
    3. Click "Get Prediction."

    Let's go! 🚀
    """
)


# Load Ward Data
@st.cache_data
def load_ward_data():
    csv_path = os.path.join("raw_data", "ward_demographics_boundaries.csv")
    ward_bound = pd.read_csv(csv_path)
    ward_bound['the_geom'] = ward_bound['the_geom'].apply(wkt.loads)
    return gpd.GeoDataFrame(ward_bound, geometry='the_geom', crs="EPSG:4326")

gdf = load_ward_data()

# Function to find the ward for given coordinates
@st.cache_data
def find_ward(lat, lon, geodataframe):
    point = Point(lon, lat)
    for _, row in geodataframe.iterrows():
        if row['the_geom'].contains(point):
            return row['Ward']
    return None

# Sidebar Inputs
st.sidebar.header("Configure Input Parameters")
selected_date = st.sidebar.date_input("Select a Date", datetime.today())
categories = ["Late Evening", "Early Morning", "Late Morning", "Early Noon", "Late Noon", "Early Evening"]
selected_category = st.sidebar.selectbox("Select a Time Category", categories)
api_url = st.sidebar.text_input("API URL", "https://rpp-589897242504.europe-west1.run.app/predict")

# Function to calculate middle time
def get_middle_time(category, date):
    time_ranges = {
        "Late Evening": (0, 6),
        "Early Morning": (6, 9),
        "Late Morning": (9, 12),
        "Early Noon": (12, 15),
        "Late Noon": (15, 18),
        "Early Evening": (18, 24)
    }
    start, end = time_ranges[category]
    middle_hour = (start + end) / 2
    return datetime.combine(date, datetime.min.time()) + timedelta(hours=middle_hour)

middle_time = get_middle_time(selected_category, selected_date).strftime("%Y-%m-%d %H:%M")

# Map Setup
chicago_coords = [41.8781, -87.6298]
m = folium.Map(location=chicago_coords, zoom_start=10)
colormap = cm.LinearColormap(['green', 'yellow', 'red'], vmin=0, vmax=1)

def create_layer(gdf, column):
    def style_function(feature):
        return {"fillColor": colormap(feature['properties'][column]), "color": "blue", "weight": 1, "fillOpacity": 0.6}

    folium.GeoJson(gdf, style_function=style_function).add_to(m)

# Add Layers (example: one column shown)
create_layer(gdf, "Race-White_pct")
LayerControl().add_to(m)
map_output = st_folium(m, height=550, width=700)

# Handle Map Clicks
if map_output.get("last_clicked"):
    coords = map_output["last_clicked"]
    selected_latitude, selected_longitude = coords["lat"], coords["lng"]
    selected_ward = find_ward(selected_latitude, selected_longitude, gdf)
    st.write(f"**Latitude:** {selected_latitude}, **Longitude:** {selected_longitude}")
    st.write(f"**Ward:** {selected_ward}")

# Prediction
if st.button("Get Prediction"):
    if not selected_ward:
        st.error("Please select a location on the map.")
    else:
        payload = {
            "ward": selected_ward,
            "date_of_occurrence": middle_time,
            "latitude": selected_latitude,
            "longitude": selected_longitude,
        }
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                labels = list(data["Top 5 Crimes"].keys())
                values = list(data["Top 5 Crimes"].values())
                percentages = [v * 100 for v in values]

                fig = go.Figure(go.Bar(
                    x=labels,
                    y=percentages,
                    text=[f"{p:.1f}%" for p in percentages],
                    textposition="outside",
                    marker_color="skyblue",
                ))
                fig.update_layout(
                    title="Top 5 Crimes as Percentage",
                    xaxis_title="Crimes",
                    yaxis_title="Percentage (%)",
                    template="plotly_white",
                )
                st.plotly_chart(fig)
            else:
                st.error("API Error: Could not retrieve predictions.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
