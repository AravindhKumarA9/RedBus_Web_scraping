import streamlit as st  # Import streamlit module
import pandas as pd
import pymysql

# Set up Streamlit app title and layout
st.title('RedBus Data Viewer')
st.subheader("Explore Bus Routes, Details, and Links")

# Sidebar for database connection credentials
st.sidebar.title("Database Configuration")

# Function to connect to the MySQL database and establish the database connection
def create_connection():
    return pymysql.connect(host='127.0.0.1', user='root', passwd='AK99ir18IR@', database='redbus')

# Function to fetch data from the specified query
def fetch_data(query, params=None):
    connection = create_connection()
    if params is None:
        params = ()
    df = pd.read_sql(query, connection, params=params)
    connection.close()
    return df

# Connect to database and fetch initial data
query_all = "SELECT state, route_name AS From_to_To, bus_name, departing_time AS Departure_Time, arrival_time AS Arrival_Time, bus_type FROM redbus"
df = fetch_data(query_all)

# Data selection options
st.sidebar.title("Data Display Options")

# Filter by State
state_options = ["All States"] + sorted(df['state'].unique())
selected_state = st.sidebar.selectbox("Select State", state_options)

# Modify route names query based on selected state
if selected_state == "All States":
    route_names_query = "SELECT DISTINCT route_name FROM redbus"
else:
    route_names_query = f"SELECT DISTINCT route_name FROM redbus WHERE state = '{selected_state}'"

# Fetch route names and add "All Routes" option
route_names_df = fetch_data(route_names_query)
route_names = ["All Routes"] + sorted(route_names_df['route_name'].unique())
selected_route = st.sidebar.selectbox("Select Route Name", route_names)

# Price filter slider and Star Rating based on selected route
price_min, price_max = st.sidebar.slider('Select price range (in INR):', min_value=0, max_value=5000, value=(0, 5000))
min_star_rating = st.sidebar.slider("Select Minimum Star Rating", min_value=0.0, max_value=5.0, step=0.1, value=2.5)

# Timing filter in the sidebar
timing_selection = st.sidebar.radio("Select Departure Time Range:", ["All Times", "Before 6am", "6am-12pm", "12pm-6pm", "After 6pm"])

# Set start and end time based on selection
if timing_selection == "Before 6am":
    start_time, end_time = "00:00:00", "06:00:00"
elif timing_selection == "6am-12pm":
    start_time, end_time = "06:00:00", "12:00:00"
elif timing_selection == "12pm-6pm":
    start_time, end_time = "12:00:00", "18:00:00"
elif timing_selection == "After 6pm":
    start_time, end_time = "18:00:00", "23:59:59"
else:
    start_time, end_time = None, None  # For "All Times"

# Bus Type filter in the sidebar
bus_type_options = ["All Types", "AC", "NON AC", "Seater", "Sleeper"]
selected_bus_type = st.sidebar.selectbox("Select Bus Type", bus_type_options)

# Construct the filtered query
filtered_query = """
    SELECT 
        state as State, 
        bus_name as 'Bus Name', 
        route_name as 'From to To',
        bus_type as 'Bus Types', 
        departing_time AS 'Departure Time', 
        arrival_time AS 'Arrival Time',  
        Duration, 
        star_rating as 'Star Rating', 
        fare_price as Price, 
        seat_availablity as 'Seat Availability'
    FROM redbus
    WHERE star_rating >= %s
    AND fare_price BETWEEN %s AND %s
"""
params = [min_star_rating, price_min, price_max]

# Add state and route filters to the query
if selected_state != "All States":
    filtered_query += " AND state = %s"
    params.append(selected_state)
if selected_route != "All Routes":
    filtered_query += " AND route_name = %s"
    params.append(selected_route)

# Add time filter if a specific time range is selected
if start_time and end_time:
    filtered_query += " AND departing_time BETWEEN %s AND %s"
    params.extend([start_time, end_time])

# Add bus type filter based on selection
if selected_bus_type == "AC":
    filtered_query += " AND (bus_type LIKE %s OR bus_type LIKE %s) AND bus_type NOT LIKE %s AND bus_type NOT LIKE %s"
    params.extend(["%AC%", "%A/C%", "%NON AC%", "%NON A/C%"])
elif selected_bus_type == "NON AC":
    filtered_query += " AND bus_type LIKE %s"
    params.append("%NON AC%")
elif selected_bus_type == "Seater":
    filtered_query += " AND bus_type LIKE %s"
    params.append("%Seater%")
elif selected_bus_type == "Sleeper":
    filtered_query += " AND bus_type LIKE %s"
    params.append("%Sleeper%")

# Fetch and display the filtered data
filtered_df = fetch_data(filtered_query, params=params)
st.write("## Filtered Bus Routes")
st.write(filtered_df)

# Fetch only Bus Name and Booking Link for the selected filters to display separately
link_query = """
    SELECT 
        bus_name as 'Bus Name', 
        route_link as 'Booking Link'
    FROM redbus
    WHERE star_rating >= %s
    AND fare_price BETWEEN %s AND %s
"""
link_params = [min_star_rating, price_min, price_max]
if selected_state != "All States":
    link_query += " AND state = %s"
    link_params.append(selected_state)
if selected_route != "All Routes":
    link_query += " AND route_name = %s"
    link_params.append(selected_route)
if start_time and end_time:
    link_query += " AND departing_time BETWEEN %s AND %s"
    link_params.extend([start_time, end_time])
if selected_bus_type == "AC":
    link_query += " AND (bus_type LIKE %s OR bus_type LIKE %s) AND bus_type NOT LIKE %s AND bus_type NOT LIKE %s"
    link_params.extend(["%AC%", "%A/C%", "%NON AC%", "%NON A/C%"])
elif selected_bus_type == "NON AC":
    link_query += " AND bus_type LIKE %s"
    link_params.append("%NON AC%")
elif selected_bus_type == "Seater":
    link_query += " AND bus_type LIKE %s"
    link_params.append("%Seater%")
elif selected_bus_type == "Sleeper":
    link_query += " AND bus_type LIKE %s"
    link_params.append("%Sleeper%")

link_df = fetch_data(link_query, params=link_params)

# Display Bus Name and Booking Links separately
st.write("## Booking Links for Filtered Routes")
st.write(link_df.dropna().reset_index(drop=True))

# Add download buttons for filtered data
st.download_button(
    label="Download Filtered Bus Routes as CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_bus_routes.csv",
    mime="text/csv"
)

st.download_button(
    label="Download Booking Links for Filtered Routes as CSV",
    data=link_df.to_csv(index=False),
    file_name="booking_links_filtered_routes.csv",
    mime="text/csv"
)
