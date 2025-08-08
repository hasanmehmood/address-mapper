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

def geocode_zipcode(geocoder, zipcode):
    """
    Geocode a zipcode and return lat, lon coordinates
    """
    try:
        # Add "USA" to improve geocoding accuracy for US zipcodes
        location = geocoder.geocode(f"{zipcode}, USA", timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        st.warning(f"Geocoding error for zipcode '{zipcode}': {str(e)}")
        return None, None

def process_csv_zipcodes(df):
    """
    Process the CSV dataframe and geocode zipcodes
    """
    geocoder = init_geocoder()
    
    # Initialize coordinate columns
    df['latitude'] = None
    df['longitude'] = None
    df['geocoding_status'] = 'Pending'
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    successful_geocodes = 0
    
    for index, row in df.iterrows():
        status_text.text(f'Geocoding zipcode {index + 1} of {len(df)}: {row["zipcode"]}')
        
        lat, lon = geocode_zipcode(geocoder, row['zipcode'])
        
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
    
    status_text.text(f'Geocoding complete! Successfully geocoded {successful_geocodes} out of {len(df)} zipcodes.')
    
    return df

def create_map(df):
    """
    Create a Folium map with variable-sized markers for zipcodes based on household count
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
        zoom_start=8,
        width='100%',
        height='100%'
    )
    
    # Calculate marker sizes based on household count
    min_households = valid_coords['no_of_households'].min()
    max_households = valid_coords['no_of_households'].max()
    
    # Add circles for each zipcode with variable sizes
    for index, row in valid_coords.iterrows():
        # Calculate radius based on household count (scale between 5 and 50)
        if max_households > min_households:
            normalized_size = (row['no_of_households'] - min_households) / (max_households - min_households)
            radius = 5 + (normalized_size * 45)  # Scale between 5 and 50
        else:
            radius = 25  # Default size if all values are the same
        
        # Color intensity based on household count
        if normalized_size >= 0.8:
            color = '#d73027'  # Dark red for highest
        elif normalized_size >= 0.6:
            color = '#f46d43'  # Orange-red
        elif normalized_size >= 0.4:
            color = '#fdae61'  # Orange
        elif normalized_size >= 0.2:
            color = '#fee08b'  # Light orange
        else:
            color = '#e0f3f8'  # Light blue for lowest
        
        popup_text = f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 0; color: #333;">Zipcode: {row['zipcode']}</h4>
            <p style="margin: 5px 0;"><b>Households:</b> {row['no_of_households']:,}</p>
            <p style="margin: 5px 0;"><b>Coordinates:</b> {row['latitude']:.4f}, {row['longitude']:.4f}</p>
        </div>
        """
        
        # Add circle marker
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"Zipcode: {row['zipcode']} | Households: {row['no_of_households']:,}",
            color='#333333',
            weight=2,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(m)
        
        # Add household count label on the circle
        # Format the number for better readability
        if row['no_of_households'] >= 1000:
            count_label = f"{row['no_of_households']/1000:.1f}K"
        else:
            count_label = str(row['no_of_households'])
            
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 11px; font-weight: bold; color: white; text-shadow: 1px 1px 2px black; text-align: center; line-height: 1;">{count_label}</div>',
                icon_size=(50, 20),
                icon_anchor=(25, 10)
            )
        ).add_to(m)
    
    # Add a legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px;">
    <h4 style="margin: 0 0 10px 0;">Household Count</h4>
    <i style="background:#d73027; width: 15px; height: 15px; float: left; margin-right: 8px; border-radius: 50%;"></i>
    High ({max_households:,})<br>
    <i style="background:#fdae61; width: 15px; height: 15px; float: left; margin-right: 8px; border-radius: 50%; margin-top: 5px;"></i>
    Medium<br>
    <i style="background:#e0f3f8; width: 15px; height: 15px; float: left; margin-right: 8px; border-radius: 50%; margin-top: 5px;"></i>
    Low ({min_households:,})<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def main():
    st.title("🗺️ Zipcode Household Mapper")
    st.markdown("Upload a CSV file with zipcodes and household counts to visualize them on an interactive map!")
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Upload CSV File**: Your CSV should contain columns:
           - `zipcode`: ZIP/Postal code (e.g., 10001)
           - `no_of_households`: Number of households in that zipcode
        
        2. **View Results**: The app will:
           - Geocode each zipcode to get coordinates
           - Show variable-sized circles based on household count
           - Display color-coded markers (red = high, blue = low)
           - Show zipcode labels on the map
        
        3. **Interactive Features**:
           - Click circles for detailed popup info
           - Hover for quick household count
           - Legend shows household count ranges
        """)
        
        st.header("📝 Sample CSV Format")
        sample_data = {
            'zipcode': ['10001', '90210', '94043'],
            'no_of_households': [2500, 1800, 3200]
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
            required_columns = ['zipcode', 'no_of_households']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                st.info("Please ensure your CSV has all required columns: zipcode, no_of_households")
                return
            
            # Display uploaded data
            st.subheader("📊 Uploaded Data")
            st.dataframe(df, use_container_width=True)
            st.info(f"Found {len(df)} zipcodes to process")
            
            # Process zipcodes button
            if st.button("🚀 Process Zipcodes and Create Map", type="primary"):
                with st.spinner("Processing zipcodes..."):
                    # Process the zipcodes
                    processed_df = process_csv_zipcodes(df.copy())
                    
                    # Store in session state for later use
                    st.session_state['processed_data'] = processed_df
                
                # Show results
                st.subheader("📈 Geocoding Results")
                
                success_count = len(processed_df[processed_df['geocoding_status'] == 'Success'])
                failed_count = len(processed_df[processed_df['geocoding_status'] == 'Failed'])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Zipcodes", len(processed_df))
                with col2:
                    st.metric("Successfully Geocoded", success_count)
                with col3:
                    st.metric("Failed to Geocode", failed_count)
                with col4:
                    total_households = processed_df[processed_df['geocoding_status'] == 'Success']['no_of_households'].sum()
                    st.metric("Total Households", f"{total_households:,}")
                
                # Show failed zipcodes if any
                if failed_count > 0:
                    st.warning(f"{failed_count} zipcodes could not be geocoded")
                    failed_zipcodes = processed_df[processed_df['geocoding_status'] == 'Failed']
                    with st.expander("View Failed Zipcodes"):
                        st.dataframe(failed_zipcodes[['zipcode', 'no_of_households']], use_container_width=True)
                
                # Create and display map
                if success_count > 0:
                    st.subheader("🗺️ Zipcode Household Map")
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
                            file_name="geocoded_zipcodes.csv",
                            mime="text/csv"
                        )
                        
                        # Show processed data
                        with st.expander("View Processed Data"):
                            st.dataframe(processed_df, use_container_width=True)
                else:
                    st.error("No zipcodes were successfully geocoded. Please check your zipcode data.")
        
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
            'zipcode': ['10001', '90210', '94043', '60601', '33101'],
            'no_of_households': [2500, 1800, 3200, 4100, 2900]
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
