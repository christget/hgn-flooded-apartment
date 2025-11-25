import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.express as px

def get_dataset():
    return pd.read_csv("dataset/apartment-dataset.csv") 

st.set_page_config(page_title='Flooded Area', page_icon='🌧', layout='wide')

noi_df = get_dataset()

st.title('🌧 Flooded Area')

st.sidebar.header('Geo Selection')
province = st.sidebar.multiselect('จังหวัด', options=noi_df['province'].unique().tolist())

district_options_df = noi_df
if province:
    district_options_df = district_options_df[district_options_df['province'].isin(province)]
district = st.sidebar.multiselect('อำเภอ/เขต', options=district_options_df['district'].unique().tolist())

sub_district_options_df = district_options_df
if district:
    sub_district_options_df = sub_district_options_df[sub_district_options_df['district'].isin(district)]
sub_district = st.sidebar.multiselect('ตำบล/แขวง', 
    options=sub_district_options_df['subDistrict'].unique().tolist()
)

st.sidebar.header('Customer Selection')
validated_type = st.sidebar.multiselect('Validated Type', options=noi_df['validatedType'].unique().tolist())
is_customer = st.sidebar.multiselect('Is Customer', options=noi_df['isCustomer'].unique().tolist())

filter_df = noi_df.copy()
if province:
    filter_df = filter_df[filter_df['province'].isin(province)]
if district:
    filter_df = filter_df[filter_df['district'].isin(district)]
if sub_district:
    filter_df = filter_df[filter_df['subDistrict'].isin(sub_district)]
if validated_type:
    filter_df = filter_df[filter_df['validatedType'].isin(validated_type)]
if is_customer:
    filter_df = filter_df[filter_df['isCustomer'].isin(is_customer)]

sub_district_geojson_file = 'subdistricts.geojson'

with open(sub_district_geojson_file) as f:
    sub_district_geojson_data = json.load(f)
for feature in sub_district_geojson_data['features']:
    feature['properties']['address'] = feature['properties']['tam_en'] + ', ' + feature['properties']['amp_en'] + ', ' + feature['properties']['pro_en']

sub_provinces = [feature['properties']['address'] for feature in sub_district_geojson_data['features'] if feature['properties']['pro_en'] in (filter_df['province'].unique())]
sub_district_df = pd.DataFrame(sub_provinces, columns=['address'])

noi_df['address'] = noi_df['subDistrict'] + ', ' + noi_df['district'] + ', ' + noi_df['province']
merged_df = sub_district_df.merge(noi_df, on='address', how='left')
merged_df['subDistrict'] = merged_df.apply(lambda row: row['subDistrict'] if pd.notna(row['subDistrict']) else row['address'].split(',')[0].strip(), axis=1)


CONSTRUCTION_COST_PER_SQM = 50000  # Average cost in THB for a medium-quality apartment building
BUILDING_USEFUL_LIFE = 70


if 'latitude' in filter_df.columns and 'longitude' in filter_df.columns:

    scatter_df = filter_df.copy()

    required_columns = [
        'name', 
        'latitude', 
        'longitude', 
        'totalFloor', 
        'numOfRooms', 
        'apartmentType', 
        'owner_name',
        'tel',
        'email',
        'validatedType',
        'isCustomer'
    ]
    scatter_df.dropna(subset=required_columns, inplace=True)

    
    if not scatter_df.empty:
        custom_data_cols = ['totalFloor', 'numOfRooms', 'apartmentType', 'owner_name', 'tel', 'email', 'validatedType', 'isCustomer']
        scatter_fig = px.scatter_mapbox(scatter_df,
                                        lat="latitude",
                                        lon="longitude",
                                        color="isCustomer",
                                        hover_name='name',
                                        custom_data=custom_data_cols, # Pass value to custom_data for hovertemplate
                                        mapbox_style="carto-positron",#mapbox_style="carto-darkmatter",
                                        zoom=7,
                                        center={"lat": scatter_df['latitude'].median(), "lon": scatter_df['longitude'].median()},
                                        height=600
                                        )
        
        scatter_fig.update_traces(
            hovertemplate=(
                "<b>%{hovertext}</b><br><br>"
                "<b>Total Floor:</b> %{customdata[0]}<br>"
                "<b>Number of Rooms:</b> %{customdata[1]}<br>"
                "<b>Apartment Type:</b> %{customdata[2]}<br>"
                "<b>Owner Name:</b> %{customdata[3]}<br>"
                "<b>Tel:</b> %{customdata[4]}<br>"
                "<b>Email:</b> %{customdata[5]}<br>"
                "<b>Validated Type:</b> %{customdata[6]}<br>"
                "<b>Is Customer:</b> %{customdata[7]}<br>"
                "<extra></extra>"
            ),
            marker=dict(size=15)
        )

        scatter_fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            hoverlabel=dict(
                bgcolor="white",    # Background color of the hoverlabel
                font_size=16,       # Set the font size
                # font_family="Rockwell" # Optional: set the font family
            )
        )
        st.plotly_chart(scatter_fig, use_container_width=True)
    else:
        st.warning("No data available with a valid 'value' for the selected filters to display on the scatter map.")
else:
    st.error("The dataset must contain 'latitude' and 'longitude' columns to display the individual apartment map.")