### Region

def regions_view():

    import streamlit as st
    import pandas as pd
    import psycopg2
    import plotly.express as px
    from supabase import create_client, Client
    import plotly.io as pio
    import io

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

    def fetch_affiliations(search_text, type_filter, topic_filter, major_code, specialty_code, from_year, to_year):
        conditions = []
        
        # Remove commas from the input search text
        search_text = search_text.replace(',', '')

        # Parse the search_text for multiple search queries separated by semicolons
        search_queries = [query.strip() for query in search_text.split(';')]
        
        query_conditions = []
        
        for query in search_queries:
            # Check if the query is within quotes for exact order
            if '"' in query:
                exact_phrases = [phrase.strip('"') for phrase in query.split('"') if phrase]
                for phrase in exact_phrases:
                    query_conditions.append(f"affiliations ILIKE '%{phrase}%'")
            else:
                # Split the query by spaces for unordered search terms
                terms = query.split()
                term_conditions = [f"affiliations ILIKE '%{term}%'" for term in terms]
                query_conditions.append(f"({' AND '.join(term_conditions)})")

        # Combine all query conditions with OR
        conditions.append(f"({' OR '.join(query_conditions)})")

        if type_filter:
            conditions.append(f"publication_type ILIKE '%{type_filter}%'")
        
        if title_filter:
            titles = title_filter.split(',')
            title_conditions = [f"title ILIKE '%{title.strip()}%'" for title in titles]
            conditions.append(f"({' OR '.join(title_conditions)})")
        
        if major_code != "All":
            if specialty_code == "All":
                conditions.append(f"topic_codes ILIKE '%{major_code}%'")
            else:
                conditions.append(f"topic_codes ILIKE '%{specialty_code}%'")
        
        conditions.append(f"year >= {from_year}")
        conditions.append(f"year <= {to_year}")
        
        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT year, COUNT(*) as publication_count, SUM(citations) as total_citations, AVG(citations) as avg_citations_per_paper
            FROM vetu_paper
            WHERE {where_clause}
            GROUP BY year
            ORDER BY year;
        """
        
        conn = create_conn()
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df

    # Create a Streamlit page for affiliation search
    st.subheader("Affiliation Search")

    col1, col2 = st.columns(2)
    with col1:
        # Create a year range slider
        year_range = st.slider('Year range:', min_value=1990, max_value=2024, value=(1990, 2024))
        fran_ar, till_ar = year_range

    with col2: 
        st.write("")
        st.write("")
        additional_filters = st.checkbox("Lägg till fler filter")

    if additional_filters:
        # Additional filters for article type and topic
        col3, col4 = st.columns(2)
        col5, col6 = st.columns(2)
        with col3:
            user_type_input = st.selectbox(
                f"Select article type",
                options=["All", "Case Reports", "Journal Article", "Clinical Trial", "Evaluation Study", "Randomized Controlled Trial", "Observational Study", "Systematic Review", "Meta-Analysis"],
            )
            type_filter = "" if user_type_input == "All" else user_type_input

        with col4:
            user_title_input = st.text_input(
                f"Filter for Title containing:",
            )
            title_filter = user_title_input if user_title_input else ""

        with col5:
            selected_major_area = st.selectbox("Select Major Area", major_areas)

        with col6:
            if selected_major_area == "All":
                selected_specialty = st.selectbox("Select Specialty", ["All"])
                major_code = "All"
                specialty_code = "All"
            else:
                # Filter specialties based on selected major area
                major_code = topic_codes_df[topic_codes_df['Swedish'] == selected_major_area]['Code'].values[0]
                filtered_specialties = sorted(topic_codes_df[topic_codes_df['Code'].str.startswith(major_code) & (topic_codes_df['Code'].str.len() == 5)]['Swedish'].unique())
                filtered_specialties.insert(0, "All")
                selected_specialty = st.selectbox("Select Specialty", filtered_specialties)
                if selected_specialty == "All":
                    specialty_code = "All"
                elif not topic_codes_df[topic_codes_df['Swedish'] == selected_specialty].empty:
                    specialty_code = topic_codes_df[topic_codes_df['Swedish'] == selected_specialty]['Code'].values[0]
                else:
                    specialty_code = ""

    else:
        title_filter = ""
        type_filter = ""
        major_code = "All"
        specialty_code = "All"

    # Create a text input for search terms
    search_text = st.text_input("Enter search terms (use semicolons to separate multiple queries):")

    # Add a checkbox for comparison
    compare = st.checkbox("Jämför", value=False)

    # Conditional second search bar for comparison
    if compare:
        search_text_2 = st.text_input("Enter search terms for comparison (use semicolons to separate multiple queries):")
    else:
        search_text_2 = ""

    # Function to create the bar chart for publication count
    def create_publications_chart(data1, data2, title):
        data1['Search'] = 'Search 1'
        if not data2.empty:
            data2['Search'] = 'Search 2'
            combined_data = pd.concat([data1, data2])
        else:
            combined_data = data1

        fig = px.bar(combined_data, x='year', y='publication_count', color='Search', barmode='group',
                    title=title, labels={'year': 'Year', 'publication_count': 'Number of Publications', 'Search': 'Search Query'})
        fig.update_layout(
            xaxis=dict(
                tickmode='linear',
                tick0=fran_ar,
                dtick=1,
                range=[fran_ar-0.5, till_ar+0.5]  # Use selected from_year and to_year for range
            ),
            legend_title_text='Affiliation'
        )
        return fig

    # Function to create the bar chart for total citations
    def create_citations_chart(data1, data2, title):
        data1['Search'] = 'Search 1'
        if not data2.empty:
            data2['Search'] = 'Search 2'
            combined_data = pd.concat([data1, data2])
        else:
            combined_data = data1

        fig = px.bar(combined_data, x='year', y='total_citations', color='Search', barmode='group',
                    title=title, labels={'year': 'Year', 'total_citations': 'Total Citations', 'Search': 'Search Query'})
        fig.update_layout(
            xaxis=dict(
                tickmode='linear',
                tick0=fran_ar,
                dtick=1,
                range=[fran_ar-0.5, till_ar+0.5]  # Use selected from_year and to_year for range
            ),
            legend_title_text='Affiliation'
        )
        return fig

    # Function to create the bar chart for average citations per paper
    def create_avg_citations_chart(data1, data2, title):
        data1['Search'] = 'Search 1'
        if not data2.empty:
            data2['Search'] = 'Search 2'
            combined_data = pd.concat([data1, data2])
        else:
            combined_data = data1

        fig = px.bar(combined_data, x='year', y='avg_citations_per_paper', color='Search', barmode='group',
                    title=title, labels={'year': 'Year', 'avg_citations_per_paper': 'Average Citations per Paper', 'Search': 'Search Query'})
        fig.update_layout(
            xaxis=dict(
                tickmode='linear',
                tick0=fran_ar,
                dtick=1,
                range=[fran_ar-0.5, till_ar+0.5]  # Use selected from_year and to_year for range
            ),
            legend_title_text='Affiliation'
        )
        return fig

    # Fetch the data based on the search terms
    if search_text:
        data1 = fetch_affiliations(search_text, type_filter, title_filter, major_code, specialty_code, fran_ar, till_ar)
        if search_text_2:
            data2 = fetch_affiliations(search_text_2, type_filter, title_filter, major_code, specialty_code, fran_ar, till_ar)
        else:
            data2 = pd.DataFrame()

        # Display the publication count chart
        if not data1.empty:
            fig1 = create_publications_chart(data1, data2, 'Publications Over Time')
            st.plotly_chart(fig1)
            
            # Display the total citations chart
            fig2 = create_citations_chart(data1, data2, 'Total Citations Over Time')
            st.plotly_chart(fig2)

            # Display the average citations per paper chart
            fig3 = create_avg_citations_chart(data1, data2, 'Average Citations per Paper Over Time')
            st.plotly_chart(fig3)
            
            # Add download buttons for the charts
            pdf_buffer1 = io.BytesIO()
            fig1.write_image(pdf_buffer1, format='pdf')
            pdf_buffer1.seek(0)
            st.download_button(
                label="Download publications chart as PDF",
                data=pdf_buffer1,
                file_name="publications_chart.pdf",
                mime="application/pdf"
            )
            
            pdf_buffer2 = io.BytesIO()
            fig2.write_image(pdf_buffer2, format='pdf')
            pdf_buffer2.seek(0)
            st.download_button(
                label="Download total citations chart as PDF",
                data=pdf_buffer2,
                file_name="citations_chart.pdf",
                mime="application/pdf"
            )

            pdf_buffer3 = io.BytesIO()
            fig3.write_image(pdf_buffer3, format='pdf')
            pdf_buffer3.seek(0)
            st.download_button(
                label="Download average citations per paper chart as PDF",
                data=pdf_buffer3,
                file_name="avg_citations_chart.pdf",
                mime="application/pdf"
            )
        else:
            st.write("No data available for the given search terms and year range.")
    else:
        st.write("Enter search terms to filter the affiliations.")