import streamlit as st
import json
import os
import time
import rasterio
from datetime import datetime
import glob
from PIL import Image
import backend
import numpy as np
from streamlit_image_select import image_select
from streamlit_folium import st_folium
import folium


# Function to display the video
def play_video(video_path):
    st.video(video_path)

# Define date range constraints
MIN_DATE = datetime.strptime("01-2014", "%m-%Y")
MAX_DATE = datetime.strptime("01-2024", "%m-%Y")

# Style Enhancements
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 10px 24px;
        font-size: 16px;
    }
    .stTextInput>div>div>input {
        padding: 10px;
    }
    .stProgress>div>div>div {
        background-color: #4CAF50;
    }
    .stAlert {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page 1: Form Input
if 'page' not in st.session_state:
    st.session_state.page = 'input'

if st.session_state.page == 'input':
    # Display the logo at the top of the page

    st.title("🛰️ DSRS: Analysis of Nighttime Satellite Images")

    st.write("Welcome to the DSRS tool! Please enter the required details below to analyze nighttime satellite images of a specific area over a given time period.")

    # Coordinate Input
    st.header("🌍 Enter the coordinates of the location")
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.text_input("Latitude", placeholder="e.g., 40.1023")
    with col2:
        longitude = st.text_input("Longitude", placeholder="e.g., -88.2275")

    # Area Input
    st.header("📏 Enter the dimensions of the area to be extracted")
    col3, col4 = st.columns(2)
    with col3:
        length = st.text_input("Length (meters)", placeholder="e.g., 100000")
    with col4:
        breadth = st.text_input("Width (meters)", placeholder="e.g., 100000")

    # Time Period Input
    st.header("📅 Enter the time period")
    col5, col6 = st.columns(2)
    with col5:
        from_date = st.text_input("From (MM-YYYY)", placeholder="e.g., 12-2016")
    with col6:
        to_date = st.text_input("To (MM-YYYY)", placeholder="e.g., 08-2024")

    # Validate inputs
    valid_inputs = True
    user_data = {}
    
    # Coordinate Input Validation
    try:
        if latitude:
            latitude = float(latitude)
            if -90 <= latitude <= 90:
                user_data['latitude'] = latitude
            else:
                st.error("Latitude must be between -90 and 90.")
                valid_inputs = False
        if longitude:
            longitude = float(longitude)
            if -180 <= longitude <= 180:
                user_data['longitude'] = longitude
            else:
                st.error("Longitude must be between -180 and 180.")
                valid_inputs = False
    except ValueError:
        st.error("Latitude and Longitude must be numerical values.")
        valid_inputs = False

    # Area Input Validation
    try:
        if length:
            length = int(length)
            if length > 0:
                user_data['length'] = length
            else:
                st.error("Length must be a positive numerical value.")
                valid_inputs = False
        if breadth:
            breadth = int(breadth)
            if breadth > 0:
                user_data['breadth'] = breadth
            else:
                st.error("Width must be a positive numerical value.")
                valid_inputs = False
    except ValueError:
        st.error("Length and Width must be numerical values.")
        valid_inputs = False

    # Time Period Input Validation
    try:
        if from_date:
            from_date = datetime.strptime(from_date, "%m-%Y")
            if MIN_DATE <= from_date <= MAX_DATE:
                user_data['from_date'] = from_date.strftime("%m-%Y")
            else:
                st.error("From date must be between 01-2014 and 01-2024.")
                valid_inputs = False
        if to_date:
            to_date = datetime.strptime(to_date, "%m-%Y")
            if MIN_DATE <= to_date <= MAX_DATE:
                if from_date and to_date < from_date:
                    st.error("End date cannot be before the start date.")
                    valid_inputs = False
                user_data['to_date'] = to_date.strftime("%m-%Y")
            else:
                st.error("To date must be between 01-2014 and 01-2024.")
                valid_inputs = False
    except ValueError:
        st.error("Dates must be in the format MM-YYYY.")
        valid_inputs = False

    # Buttons for Submit and View Results
    col7, col8 = st.columns([1, 1])  # Adjust column widths if needed

    with col7:
        if valid_inputs:
            if st.button('Submit'):
                # Save JSON data to a file
                file_name = "user_data.json"
                with open(file_name, "w") as f:
                    json.dump(user_data, f, indent=4)
                st.success(f"Data saved to {file_name}")

                # Run backend script
                try:
                    backend.extract_all()
                    #subprocess.run(["python", backend_script_path], check=True)
                    st.success("Backend script executed successfully.")
                except Exception as e:
                    st.error(f"Error running backend script: {e}")
    
    with col8:
        if valid_inputs:
            if st.button('View Results'):
                # Show a 35-second progress bar after submission
                #progress_bar = st.progress(0)
                #for percent_complete in range(100):
                #    time.sleep(0.35)  # Simulate a 35-second delay with incremental updates
                #    progress_bar.progress(percent_complete + 1)

                # Transition to results page
                st.session_state.page = 'results'


elif st.session_state.page == 'results':
    # Display the logo at the top of the page

    # Load input data from the saved JSON file
    file_name = "user_data.json"
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            user_data = json.load(f)
    else:
        st.error(f"User input data file not found at {file_name}")
        st.stop()  # Stop execution if the file is not found

    # Title with icon
    st.title("📊 DSRS - Analysis Results")

    # Introduction to the results page with colored info box
    st.markdown(
        """
        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; font-size: 16px;">
        <strong>Analysis Complete!</strong> Below are the results of your nighttime satellite image analysis.
        You can view the summary of input parameters and detailed results.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Section 1: Summary of Results
    with st.expander("📋 Summary of Input Parameters", expanded=True):
        st.write("Here is a quick summary of the selected coordinates, area  and time period.")
        
        # Display coordinates and time range as bullet points
        st.markdown(
            f"""
            - **Latitude:** {user_data.get('latitude', 'N/A')}
            - **Longitude:** {user_data.get('longitude', 'N/A')}
            - **Area Dimensions:** {user_data.get('length', 'N/A')} x {user_data.get('breadth', 'N/A')} (Length x Width)
            - **Time Period:** {user_data.get('from_date', 'N/A')} to {user_data.get('to_date', 'N/A')}
            """
        )

    st.markdown("---")

    # Section 2: Detailed Results (Images, Graphs, and Videos)
    with st.expander("📊 Detailed Results", expanded=True):
        st.write("Explore the change in average pixel intensity over the given time.")
        
        # Image section with description
        st.subheader("📈 Intensity Graph")
        image_path = "./Extracted_images/graph.png"
        if os.path.exists(image_path):
            st.image(image_path, use_column_width=True)
        else:
            st.error(f"Image file not found at {image_path}")

        # Divider between sections
        st.markdown("---")

        # Video section with description
# Display the video section without the caption argument
        st.subheader("🎥 Visualization of changes over time ")
        video_path = "./Extracted_images/output_video.mp4"
        if os.path.exists(video_path):
            st.video(video_path, start_time=0)  # Removed the 'caption' argument
        else:
            st.error(f"Video file not found at {video_path}")


    st.markdown("---")
    all_images = glob.glob("Extracted_images/*.tif")
    def convert_image(path, min_val=None, max_val=None):
        with Image.open(path) as img:
            img_array = np.array(img)
            img_8bit_array = ((img_array - img_array.min()) / (img_array.max() - img_array.min()) * 255).astype(np.uint8)
            img_8bit = Image.fromarray(img_8bit_array)
        return img_8bit
    ii = np.array(convert_image(all_images[0]))
    #st.image(ii, caption='Extracted Image', clamp=True)
    img = image_select(
        label="Select an image",
        images=[convert_image(i) for i in all_images],
        captions=[os.path.basename(i) for i in all_images],
        use_container_width=False,
        return_value='index'
    )
    st.markdown("---")
    values = st.slider("Select a range of values", 0.0, 255.0, (0.0, 100.0))
    alpha = st.slider("Select the opacity", 0.0, 1.0, 0.8, step=0.1)
    m = folium.Map(location=[user_data['latitude'], user_data['longitude']], zoom_start=8, tiles="Cartodb Positron")
    with rasterio.open(all_images[img]) as src:
        bounds = src.bounds
        folium_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
    temp = np.array(convert_image(all_images[img]))
    temp = temp.clip(int(values[0]), int(values[1]))
    image = folium.raster_layers.ImageOverlay(
        image=temp,
        bounds=folium_bounds,
        opacity=alpha,
        interactive=True,
        z_index=1,
        name='Extracted Image'
    ).add_to(m)

    with open(all_images[img], "rb") as file:
        btn = st.download_button(
            label="Download image",
            data=file,
            file_name=os.path.basename(all_images[img]),
            mime="image/tif",
        )
    st_data = st_folium(m, width=600, height=600)
    st.markdown("---")

    # Button to go back to the input page
    if st.button('🔙 Back to Input Page'):
        st.session_state.page = 'input'
