### Funding
def funding_view():

    import streamlit as st
    import pandas as pd
    import psycopg2
    import matplotlib.pyplot as plt
    import plotly.express as px
    from supabase import create_client, Client
    import plotly.io as pio
    import io
    from pathlib import Path

    pio.templates.default = "ggplot2"

    # Accessing Supabase secrets
    secrets = st.secrets["supabase"]

    # Function to create a connection to the PostgreSQL database
    def create_conn():
        conn = psycopg2.connect(
            host=secrets["host_hidden"],
            dbname=secrets["db_hidden"],
            user=secrets["user_hidden"],
            password=secrets["password_hidden"],
            port=secrets["port_hidden"]
        )
        return conn

    # Construct file paths using Pathlib
    file_path_university = 'affiliations_university_norm.csv'
    file_path_university2 = 'affiliations_university_decoder_list.csv'
    file_path_topic_codes = 'Topic_Codes.csv'

    # Read the CSV files
    try:
        df_university = pd.read_csv(file_path_university)
        df_university2 = pd.read_csv(file_path_university2)
    except Exception as e:
        st.error(f"Error loading files: {e}")

    # Load university data
    universities = pd.read_csv(file_path_university)
    universities['Code'] = universities['Code'].astype(str)

    # Load university decoder list data
    universities2 = pd.read_csv(file_path_university2)
    universities2['Code'] = universities2['Code'].astype(str)

    #Import topic codes indexing
    topic_codes_df = pd.read_csv(file_path_topic_codes, sep=';')
    topic_codes_df['Code'] = topic_codes_df['Code'].astype(str)

    # Extract unique major areas and specialties
    major_areas = sorted(topic_codes_df[(topic_codes_df['Code'].str.len() == 3) & (topic_codes_df['Code'].str.startswith('3'))]['Swedish'])
    specialties = sorted(topic_codes_df[(topic_codes_df['Code'].str.len() == 5) & (topic_codes_df['Code'].str.startswith('3'))]['Swedish'])

    # Add "All" option to the dropdowns
    major_areas.insert(0, "All")
    specialties.insert(0, "All")

    st.write('Funktionen kommer snart')