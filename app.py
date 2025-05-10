import streamlit as st  # Import Streamlit for creating the web app
import geopandas as gpd  # Import GeoPandas for geospatial data handling
from shapely.validation import explain_validity  # Import function to explain invalid geometries
from streamlit_folium import st_folium  # Import st_folium for embedding Folium maps in Streamlit
import folium  # Import Folium for map visualization
from loguru import logger  # Import Loguru for logging
import concurrent.futures  # Import for parallel processing of geometries
import time  # Import time module to measure processing time
from datetime import datetime  # Import datetime for timestamps
import json  # Import json module for handling JSON data
from kafka_integration import get_kafka_producer, send_kafka_event  # Import custom Kafka integration functions

# INITIALIZE THE KAFKA PRODUCER:
# This sets up the Kafka connection using our separate module.
producer = get_kafka_producer()

# INITIALIZE SESSION STATE FOR VERSION HISTORY:
# Check if 'versions' exists in session state; if not, initialize it as an empty list.
if 'versions' not in st.session_state:
    st.session_state['versions'] = []

# CONFIGURE LOGGING:
# Set up Loguru to log messages to "app.log" with rotation after 1MB.
logger.add("app.log", rotation="1 MB")

# SET PAGE CONFIGURATION:
# Define the title and layout of the Streamlit page.
st.set_page_config(
    page_title="GeoJSON Dashboard",  # Title of the page
    layout="wide"                    # Use the wide layout for more horizontal space
)

# SET THE APPLICATION TITLE:
st.title("🌍 GeoJSON Dashboard")  # Display the main title at the top

# FILE UPLOADER:
# Create a file uploader widget that accepts files with .geojson or .json extension.
file = st.file_uploader("Upload your GeoJSON file", type=["geojson", "json"])

# DEFINE A FUNCTION FOR PARALLEL VALIDATION OF GEOMETRIES:
def parallel_validate(geom):
    """
    Validate a single geometry in parallel.
    Returns a dictionary with:
      - valid: Boolean indicating if the geometry is valid.
      - issue: Explanation if invalid, otherwise None.
      - wkt: The Well-Known Text representation of the geometry.
    """
    return {
        "valid": geom.is_valid,  # Check if the geometry is valid using Shapely
        "issue": None if geom.is_valid else explain_validity(geom),  # If not valid, provide an explanation
        "wkt": geom.wkt  # Convert geometry to its WKT representation
    }

# PROCESS THE FILE IF UPLOADED:
if file:
    try:
        # Record the start time for processing the file.
        start_time = time.time()
        
        # Read the uploaded GeoJSON file into a GeoDataFrame.
        gdf = gpd.read_file(file)
        # Log the successful file load.
        logger.info("GeoJSON file loaded successfully.")

        # SAVE VERSION INFO:
        # Create a dictionary with the file name and current timestamp, and save it in session state.
        version_info = {"filename": file.name, "timestamp": datetime.now().isoformat()}
        st.session_state['versions'].append(version_info)
        
        # DISPLAY RAW DATA PREVIEW:
        # Show a preview of the data without the geometry column (first 10 rows).
        st.subheader("📋 Data Preview (Raw Data)")
        st.dataframe(gdf.drop(columns='geometry').head(10))

        # GEOMETRY VALIDATION USING PARALLEL PROCESSING:
        st.subheader("🛠️ Geometry Validation (Parallel Processing)")
        # Use ThreadPoolExecutor to validate all geometries concurrently.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(parallel_validate, gdf.geometry))
        
        # Append the results of validation to the GeoDataFrame:
        # 'valid' column indicates whether each geometry is valid.
        # 'issue' column stores the issue explanation if any.
        gdf['valid'] = [res["valid"] for res in results]
        gdf['issue'] = [res["issue"] for res in results]
        
        # IDENTIFY INVALID GEOMETRIES:
        # Filter the GeoDataFrame to get geometries that are not valid.
        invalid_geometries = gdf[~gdf['valid']]
        if not invalid_geometries.empty:
            # Display a warning if invalid geometries are detected.
            st.warning(f"⚠️ Detected {len(invalid_geometries)} invalid geometries.")
            logger.warning(f"Detected {len(invalid_geometries)} invalid geometries.")
            # Show the issue details for the first few invalid geometries.
            st.dataframe(invalid_geometries[['issue']].head(10))
            
            # ATTEMPT TO FIX INVALID GEOMETRIES:
            # Use a zero-width buffer to attempt to correct the geometry.
            gdf['geometry_fixed'] = gdf.geometry.buffer(0)
            # Check if the fixed geometries are now valid.
            gdf['valid_fixed'] = gdf['geometry_fixed'].apply(lambda g: g.is_valid)
            # Identify any geometries that remain invalid after the fix attempt.
            still_invalid = gdf[~gdf['valid_fixed']]
            if still_invalid.empty:
                # If all geometries are fixed, update the GeoDataFrame to use the fixed geometries.
                st.success("✅ All geometries successfully fixed using buffer(0).")
                gdf.set_geometry('geometry_fixed', inplace=True, drop=True)
            else:
                # If some geometries still cannot be fixed, display an error.
                st.error(f"❌ {len(still_invalid)} geometries remain invalid after fix attempt.")
                logger.error(f"{len(still_invalid)} geometries remain invalid after attempted fixes.")
                st.dataframe(still_invalid[['geometry']].head(10))
                # Filter out the still-invalid geometries and update the GeoDataFrame.
                gdf = gdf[gdf['valid_fixed']]
                gdf.set_geometry('geometry_fixed', inplace=True, drop=True)
        else:
            # If no invalid geometries are found, display a success message.
            st.success("✅ All geometries are valid.")
            logger.info("All geometries are valid initially.")

        # DUPLICATE GEOMETRY DETECTION:
        st.subheader("🔍 Duplicate Geometry Detection")
        # Use the duplicated method to detect duplicates based on the 'geometry' column.
        duplicates = gdf.duplicated(subset='geometry', keep=False)
        duplicate_geometries = gdf[duplicates]
        if not duplicate_geometries.empty:
            # Display a warning if duplicates are found.
            st.warning(f"⚠️ Detected {len(duplicate_geometries)} duplicate geometries.")
            logger.warning(f"Detected {len(duplicate_geometries)} duplicate geometries.")
            st.dataframe(duplicate_geometries.drop(columns='geometry').head(10))
        else:
            # Display a success message if no duplicates are detected.
            st.success("✅ No duplicate geometries detected.")
            logger.info("No duplicate geometries detected.")

        # MAP VISUALIZATION:
        st.subheader("🗺️ Interactive Map")
        if not gdf.empty:
            # Calculate the centroid of all geometries to center the map.
            centroid = gdf.unary_union.centroid
            # Create a Folium map centered at the calculated centroid.
            m = folium.Map(location=[centroid.y, centroid.x], zoom_start=10)
            # Add the GeoDataFrame as a GeoJSON overlay to the map.
            folium.GeoJson(gdf).add_to(m)
            # Render the Folium map within the Streamlit app.
            st_folium(m, width=800, height=500)
            st.success("Geometries visualized successfully!")
            logger.info("Map visualization completed successfully.")
        else:
            # Display an error if there are no valid geometries to visualize.
            st.error("No valid geometries to visualize.")
            logger.error("No valid geometries to visualize after processing.")
        
        # CALCULATE AND DISPLAY PROCESSING TIME:
        processing_time = time.time() - start_time
        st.info(f"Processing time: {processing_time:.2f} seconds")
        
        # DISPLAY VERSION HISTORY:
        st.subheader("📂 Version History")
        st.dataframe(st.session_state['versions'])
        
        # SIMULATED TEAM COMMENTS SECTION:
        st.subheader("💬 Team Comments")
        # Initialize the 'comments' in session state if not already present.
        if 'comments' not in st.session_state:
            st.session_state['comments'] = []
        # Provide a text input for entering a comment.
        comment = st.text_input("Enter your comment")
        # On clicking the submit button, add the comment with a timestamp to the session state.
        if st.button("Submit Comment"):
            st.session_state['comments'].append({
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            })
        # Display the comments in a table.
        st.dataframe(st.session_state['comments'])
        
        # PUBLISH A KAFKA EVENT:
        # Create an event dictionary with details of the processed file.
        event = {
            "filename": file.name,
            "timestamp": datetime.now().isoformat(),
            "processing_time": processing_time,
            "total_features": len(gdf)
        }
        # Send the event to the Kafka topic "geojson_upload_events" using the custom function.
        send_kafka_event(producer, "geojson_upload_events", event)
        
    except Exception as e:
        # If any error occurs during processing, display an error message.
        error_message = f"Error processing GeoJSON file: {e}"
        st.error(error_message)
        # Log the exception with a traceback.
        logger.exception(error_message)
