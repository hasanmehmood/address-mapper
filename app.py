import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
import time
import io

# Configure the page
st.set_page_config(
    page_title="Address Mapper",
    page_icon="🗺️",
    layout="wide"
)

# Initialize geocoder
@st.cache_resource
def init_geocoder():
    return Nominatim(user_agent="streamlit_address_mapper")

def geocode_address(geocoder, full_address):
    """
    Geocode a full address string and return lat, lon coordinates
    """
    try:
        location = geocoder.geocode(full_address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        st.warning(f"Geocoding error for '{full_address}': {str(e)}")
        return None, None

def process_csv_addresses(df):
    """
    Process the CSV dataframe and geocode addresses
    """
    geocoder = init_geocoder()
    
    # Create full address column
    df['full_address'] = df.apply(lambda row: f"{row['street']}, {row['city']}, {row['state']} {row['zipcode']}", axis=1)
    
    # Initialize coordinate columns
    df['latitude'] = None
    df['longitude'] = None
    df['geocoding_status'] = 'Pending'
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    successful_geocodes = 0
    
    for index, row in df.iterrows():
        status_text.text(f'Geocoding address {index + 1} of {len(df)}: {row["full_address"]}')
        
        lat, lon = geocode_address(geocoder, row['full_address'])
        
        if lat and lon:
            df.at[index, 'latitude'] = lat
            df.at[index, 'longitude'] = lon
            df.at[index, 'geocoding_status'] = 'Success'
            successful_geocodes += 1
        else:
            df.at[index, 'geocoding_status'] = 'Failed'
        
        # Update progress
        progress_bar.progress((index + 1) / len(df))
        
        # Add small delay to be respectful to the geocoding service
        time.sleep(0.1)
    
    status_text.text(f'Geocoding complete! Successfully geocoded {successful_geocodes} out of {len(df)} addresses.')
    
    return df

def create_map(df):
    """
    Create a Folium map with markers for all geocoded addresses
    """
    # Filter out failed geocodes
    valid_coords = df.dropna(subset=['latitude', 'longitude'])
    
    if len(valid_coords) == 0:
        st.error("No valid coordinates found to display on the map.")
        return None
    
    # Calculate map center (average of all coordinates)
    center_lat = valid_coords['latitude'].mean()
    center_lon = valid_coords['longitude'].mean()
    
    # Create the map with larger dimensions
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=10,
        width='100%',
        height='100%'
    )
    
    # Add markers for each address
    for index, row in valid_coords.iterrows():
        popup_text = f"""
        <b>Account ID:</b> {row['account_id']}<br>
        <b>Address:</b> {row['full_address']}<br>
        <b>Coordinates:</b> {row['latitude']:.6f}, {row['longitude']:.6f}
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Account: {row['account_id']}",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)
    
    return m

def main():
    st.title("🗺️ Address Mapper")
    st.markdown("Upload a CSV file with addresses and visualize them on Google Maps!")
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Upload CSV File**: Your CSV should contain columns:
           - `account_id`: Unique identifier
           - `street`: Street address
           - `city`: City name
           - `state`: State/Province
           - `zipcode`: ZIP/Postal code
        
        2. **View Results**: The app will:
           - Geocode each address to get coordinates
           - Show a summary of successful/failed geocoding
           - Display all locations on an interactive map
        
        3. **Download Results**: Get the processed data with coordinates
        """)
        
        st.header("📝 Sample CSV Format")
        sample_data = {
            'account_id': ['ACC001', 'ACC002'],
            'street': ['1600 Amphitheatre Parkway', '1 Apple Park Way'],
            'city': ['Mountain View', 'Cupertino'],
            'state': ['CA', 'CA'],
            'zipcode': ['94043', '95014']
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)
        
        # Developer info
        st.markdown("---")
        st.header("👨‍💻 Developer")
        st.markdown("""
        **Hassan Mehmood**  
        *Data Engineer*
        
        [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/hasanmehmood/)
        
        [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hasanmehmood)
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.header("🤝 Contribute")
        st.markdown("""
        **Found a bug or have a feature request?**
        
        [![Repository](https://img.shields.io/badge/Repository-address--mapper-blue?style=for-the-badge&logo=github)](https://github.com/hasanmehmood/address-mapper)
        
        - 🐛 Report issues
        - ⭐ Star the repo
        - 🔀 Submit pull requests
        - 💡 Suggest improvements
        """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload a CSV file containing address data"
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            required_columns = ['account_id', 'street', 'city', 'state', 'zipcode']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                st.info("Please ensure your CSV has all required columns: account_id, street, city, state, zipcode")
                return
            
            # Display uploaded data
            st.subheader("📊 Uploaded Data")
            st.dataframe(df, use_container_width=True)
            st.info(f"Found {len(df)} addresses to process")
            
            # Process addresses button
            if st.button("🚀 Process Addresses and Create Map", type="primary"):
                with st.spinner("Processing addresses..."):
                    # Process the addresses
                    processed_df = process_csv_addresses(df.copy())
                    
                    # Store in session state for later use
                    st.session_state['processed_data'] = processed_df
                
                # Show results
                st.subheader("📈 Geocoding Results")
                
                success_count = len(processed_df[processed_df['geocoding_status'] == 'Success'])
                failed_count = len(processed_df[processed_df['geocoding_status'] == 'Failed'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Addresses", len(processed_df))
                with col2:
                    st.metric("Successfully Geocoded", success_count)
                with col3:
                    st.metric("Failed to Geocode", failed_count)
                
                # Show failed addresses if any
                if failed_count > 0:
                    st.warning(f"{failed_count} addresses could not be geocoded")
                    failed_addresses = processed_df[processed_df['geocoding_status'] == 'Failed']
                    with st.expander("View Failed Addresses"):
                        st.dataframe(failed_addresses[['account_id', 'full_address']], use_container_width=True)
                
                # Create and display map
                if success_count > 0:
                    st.subheader("🗺️ Address Map")
                    map_obj = create_map(processed_df)
                    
                    if map_obj:
                        # Display the map
                        st.components.v1.html(
                            map_obj._repr_html_(),
                            width=1200,
                            height=800,
                            scrolling=False
                        )
                        
                        # Download processed data
                        st.subheader("💾 Download Results")
                        
                        # Convert to CSV
                        csv_buffer = io.StringIO()
                        processed_df.to_csv(csv_buffer, index=False)
                        csv_data = csv_buffer.getvalue()
                        
                        st.download_button(
                            label="📥 Download Processed Data (CSV)",
                            data=csv_data,
                            file_name="geocoded_addresses.csv",
                            mime="text/csv"
                        )
                        
                        # Show processed data
                        with st.expander("View Processed Data"):
                            st.dataframe(processed_df, use_container_width=True)
                else:
                    st.error("No addresses were successfully geocoded. Please check your address data.")
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please make sure your CSV file is properly formatted.")
    
    else:
        # Show example when no file is uploaded
        st.info("👆 Please upload a CSV file to get started!")
        
        # Show example data
        st.subheader("🎯 Example")
        st.markdown("Here's what your CSV file should look like:")
        
        example_data = {
            'account_id': ['ACC001', 'ACC002', 'ACC003'],
            'street': ['1600 Amphitheatre Parkway', '1 Apple Park Way', '350 5th Ave'],
            'city': ['Mountain View', 'Cupertino', 'New York'],
            'state': ['CA', 'CA', 'NY'],
            'zipcode': ['94043', '95014', '10118']
        }
        example_df = pd.DataFrame(example_data)
        st.dataframe(example_df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 20px 0;'>
            <p style='margin: 0; color: #666; font-size: 14px;'>
                Built with ❤️ by <strong>Hassan Mehmood</strong> | 
                <a href='https://www.linkedin.com/in/hasanmehmood/' target='_blank' style='text-decoration: none; color: #0077B5;'>LinkedIn</a> | 
                <a href='https://github.com/hasanmehmood' target='_blank' style='text-decoration: none; color: #333;'>GitHub</a> | 
                <a href='https://github.com/hasanmehmood/address-mapper' target='_blank' style='text-decoration: none; color: #28a745;'>⭐ Repository</a>
            </p>
            <p style='margin: 5px 0 0 0; color: #888; font-size: 12px;'>
                Streamlit Address Mapper - Convert addresses to interactive maps | Open Source & MIT Licensed
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
