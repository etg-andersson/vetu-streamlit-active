### Search

def search_view():

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

    from pandas.api.types import is_categorical_dtype, is_datetime64_any_dtype, is_numeric_dtype, is_object_dtype

    # Fetch data with filters applied in the SQL query
    def fetch_author_paper_data(filters):

        # Start with the base query
        query = """
            SELECT title, publication_type, abstract_text, journal_title, affiliations, pmid 
            FROM vetu_paper
        """

        # Dynamically add WHERE clauses based on the filters
        conditions = []
        if filters.get("Type of paper"):
            type_conditions = " OR ".join([f"publication_type = '{type_}'" for type_ in filters['Type of paper']])
            conditions.append(f"({type_conditions})")
        
        if filters.get("Title"):
            conditions.append(f"title ILIKE '%{filters['Title']}%'")
        
        if filters.get("Topic"):
            if filters.get("Specialty") and filters['Specialty'] != "All":
                conditions.append(f"topic_codes ILIKE '%{filters['Specialty']}%'")
            else:
                conditions.append(f"topic_codes ILIKE '%{filters['Topic']}%'")
        
        if filters.get("Journal"):
            conditions.append(f"journal_title ILIKE '%{filters['Journal']}%'")
        
        if filters.get("Affiliation"):
            conditions.append(f"affiliations ILIKE '%{filters['Affiliation']}%'")

        # Add conditions to the query if any
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        conn = create_conn()
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Rename columns
        df.rename(columns={
            'title': 'Title',
            'publication_type': 'Type of paper',
            'abstract_text': 'Topic',
            'journal_title': 'Journal',
            'affiliations': 'Affiliation',
            'pmid': 'PmID'
        }, inplace=True)

        return df

    # UI for filtering
    def filter_dataframe() -> dict:
        filters = {}
        with st.container():
            to_filter_columns = st.multiselect("Filter articles based on", ["Type of paper", "Title", "Topic", "Journal", "Affiliation"])
            
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                if column == "Type of paper":
                    user_type_input = right.multiselect(
                        f"Select {column}",
                        options=["Case Reports", "Journal Article", "Clinical Trial", "Evaluation Study", "Randomized Controlled Trial", "Observational Study", "Systematic Review", "Meta-Analysis"],
                    )
                    if user_type_input:
                        filters[column] = user_type_input
                elif column == "Topic":

                    selected_major_area = right.selectbox("Select Major Area", major_areas)

                    if selected_major_area != "All":
                        major_code = topic_codes_df[topic_codes_df['Swedish'] == selected_major_area]['Code'].values[0]
                        filters["Topic"] = major_code
                        filtered_specialties = sorted(topic_codes_df[(topic_codes_df['Code'].str.startswith(major_code)) & (topic_codes_df['Code'].str.len() == 5)]['Swedish'])
                        filtered_specialties.insert(0, "All")

                        selected_specialty = right.selectbox("Select Specialty", filtered_specialties)
                        if selected_specialty != "All":
                            specialty_code = topic_codes_df[topic_codes_df['Swedish'] == selected_specialty]['Code'].values[0]
                            filters["Specialty"] = specialty_code
                        else:
                            filters['Specialty'] = "All"
                    else:
                        filters['Specialty'] = "All"
                else:
                    user_text_input = right.text_input(
                        f"Filter for {column} containing:",
                    )
                    if user_text_input:
                        filters[column] = user_text_input
        
        return filters

    # Filter parameters
    filters = filter_dataframe()

    search_button = st.button('Search')

    st.write('---')

    # Display matching results
    if search_button:
        # Fetch data based on filters
        author_paper_df = fetch_author_paper_data(filters)
        if not author_paper_df.empty:
            st.text(f"{len(author_paper_df)} results")
            top_50_df = author_paper_df.head(50)
            for index, row in top_50_df.iterrows():
                st.markdown(f"**Type of paper:** {row['Type of paper']}")
                st.markdown(f"**Title:** {row['Title']}")
                st.markdown(f"**Topic:** {row['Topic']}")
                st.markdown(f"**Journal:** {row['Journal']}")
                st.markdown(f"**Affiliation:** {row['Affiliation']}")
                pubmed_link = f"https://pubmed.ncbi.nlm.nih.gov/{row['PmID']}/"
                st.markdown(f"[Link to PubMed]({pubmed_link})")
                st.markdown("---")
        else:
            st.write("No matching results found.")