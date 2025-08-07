# 🗺️ Streamlit Address Mapper

A Streamlit web application that takes a CSV file containing addresses and plots them on an interactive Google Maps interface using Folium.

## Features

- **CSV File Upload**: Upload CSV files with address data
- **Address Geocoding**: Automatically convert addresses to coordinates using OpenStreetMap (via Nominatim)
- **Interactive Map**: Display all addresses as markers on an interactive map
- **Progress Tracking**: Real-time progress indication during geocoding
- **Error Handling**: Identify and report addresses that couldn't be geocoded
- **Data Download**: Download the processed data with coordinates
- **Responsive Design**: Clean, modern UI with sidebar instructions

## CSV Format

Your CSV file should contain the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `account_id` | Unique identifier | ACC001 |
| `street` | Street address | 1600 Amphitheatre Parkway |
| `city` | City name | Mountain View |
| `state` | State/Province | CA |
| `zipcode` | ZIP/Postal code | 94043 |

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your web browser to the provided URL (usually `http://localhost:8501`)

3. Upload your CSV file using the file uploader

4. Click "Process Addresses and Create Map" to:
   - Geocode all addresses
   - Display results summary
   - Show interactive map with markers
   - Provide download link for processed data

## Sample Data

A sample CSV file (`sample_addresses.csv`) is included with example addresses from well-known tech companies.

## Technical Details

### Libraries Used

- **Streamlit**: Web app framework
- **Pandas**: Data manipulation
- **Folium**: Interactive maps
- **Geopy**: Geocoding service (using Nominatim/OpenStreetMap)

### Geocoding Service

This app uses Nominatim (OpenStreetMap's geocoding service) which is free and doesn't require an API key. For production use with large datasets, consider:

- Google Maps Geocoding API (requires API key, paid service)
- MapBox Geocoding API (requires API key, has free tier)
- Here Geocoding API (requires API key, has free tier)

### Rate Limiting

The app includes a small delay (0.1 seconds) between geocoding requests to be respectful to the free Nominatim service.

## Customization

You can easily modify the app to:

- Use different geocoding services (Google Maps, MapBox, etc.)
- Change map styling and marker icons
- Add more address fields
- Implement clustering for large datasets
- Add export options (KML, GeoJSON, etc.)

## Troubleshooting

**Geocoding Failures**: Some addresses may fail to geocode due to:
- Incomplete or incorrect address data
- Addresses not found in OpenStreetMap database
- Network connectivity issues

**Performance**: For large datasets (1000+ addresses), consider:
- Using a paid geocoding service with higher rate limits
- Implementing batch geocoding
- Adding caching for previously geocoded addresses

## License

This project is open source and available under the MIT License.
