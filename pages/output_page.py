import streamlit as st
import requests
import plotly.graph_objects as go

# Output Page: Displaying predictions and visualizations
st.title("PredPol 2.0 - Output Page")

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
    if st.sidebar.button("Get Prediction"):
        if api_url and selected_ward and middle_time and selected_latitude and selected_longitude:
        # Prepare API request payload
            payload = {
                "ward": selected_ward,
                "date_of_occurrence": middle_time,
                "latitude": selected_latitude,
                "longitude": selected_longitude,
        }
        st.sidebar.write("### Payload Sent to API")
        st.json(payload)
        try:
            # Make API request
            response = requests.post(api_url, json=payload)
            response_data = response.json()

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
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.sidebar.error("Failed to retrieve a valid prediction. Please check your inputs or API.")
        except Exception as e:
            st.sidebar.error(f"An error occurred: {e}")
    else:
        st.sidebar.warning("Please ensure all parameters are filled out correctly.")
