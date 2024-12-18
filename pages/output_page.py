import streamlit as st
import requests
import plotly.express as px

# Output Page: Displaying predictions and visualizations
st.title("Risky Predictive Web App - Output Page")

# Retrieving inputs from session state
selected_ward = st.session_state.get("selected_ward")
middle_time = st.session_state.get("middle_time")
selected_latitude = st.session_state.get("selected_latitude")
selected_longitude = st.session_state.get("selected_longitude")
api_url = st.session_state.get("api_url")

# Checking if all inputs are provided
if all([selected_ward, middle_time, selected_latitude, selected_longitude, api_url]):
    st.write("### Your Inputs")
    st.write(f"**Ward:** {selected_ward}")
    st.write(f"**Date of Occurrence:** {middle_time}")
    st.write(f"**Latitude:** {selected_latitude}")
    st.write(f"**Longitude:** {selected_longitude}")

    # API call and Get Prediction
    if st.button("Get Prediction"):
        payload = {
            "ward": selected_ward,
            "date_of_occurrence": middle_time,
            "latitude": selected_latitude,
            "longitude": selected_longitude,
        }
        st.write("### Payload Sent to API")
        st.json(payload)

        try:
            # Make API request
            response = requests.post(api_url, json=payload)
            response_data = response.json()

            if response.status_code == 200:

                # Displaying Offense Count Prediction (Regression Output)
                offense_count = response_data.get("offense_count", None)
                if offense_count is not None:
                    st.write("### Predicted Offense Count")
                    st.success(f"The predicted number of offenses is approximately: {offense_count:.0f}")
                else:
                    st.warning("No offense count prediction available.")

                # Visualization logic (Top 5 Crimes)
                top_crimes = response_data.get('Top 5 Crimes', {})
                if top_crimes:
                    labels = list(top_crimes.keys())
                    values = list(top_crimes.values())

                    # Create the bar chart
                    fig = px.bar(
                        x=labels,
                        y=values,
                        labels={'x': 'Crimes', 'y': 'Frequency'},
                        title="Top 5 Crimes",
                        text=values
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    fig.update_traces(texttemplate='%{text}', textposition='outside')

                    # Display the chart
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No crime data available in the response.")
            else:
                st.error("Failed to retrieve a valid prediction. Please check your inputs or API.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.warning("Please provide inputs on the Input Page before accessing predictions.")
