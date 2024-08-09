### Journal

def journal_view():

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
    st.subheader('Top journals by filter')

    from pandas.api.types import (
        is_categorical_dtype,
        is_datetime64_any_dtype,
        is_numeric_dtype,
        is_object_dtype,
    )


    # Function to fetch data from the database
    def fetch_data_tidsskrift():
        conn = create_conn()
        query = "SELECT title, publication_type, abstract_text, affiliation_codes, journal_title, year FROM vetu_paper"
        df = pd.read_sql_query(query, conn)
        conn.close()
        # Rename columns
        df.rename(columns={
            'title': 'Title',
            'publication_type': 'Type',
            'abstract_text': 'Topic',
            'affiliation_codes': 'Affiliation',
            'journal_title': 'Journal',
            'year': 'Year'
        }, inplace=True)
        return df

    def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.columns:
            if is_object_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass
            if is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)
        
        modification_container = st.container()
        with modification_container:
            filter_columns = [col for col in df.columns if col != 'Journal']
            to_filter_columns = st.multiselect("Filter results based on", filter_columns, default=['Year'])
            for column in to_filter_columns:
                left, right = st.columns((1, 20))

                if column == "Type":
                    user_type_input = right.selectbox(
                        f"Select {column}",
                        options=df[column].unique(),
                    )
                    df = df[df[column] == user_type_input]

                elif column == "Affiliation": 
                    selected_university = right.selectbox('Universitet:', ["All"] + universities2[universities2['Code'].str.count('\.') == 0]['Department'].tolist(), index=0) # Universitet
                    if selected_university != "All":
                        selected_university_code = universities2[universities2['Department'] == selected_university]['Code'].values[0]
                        selected_institute = right.selectbox('Institut:',
                        ["All"] + universities2[
                            (universities2['Code'].str.startswith(selected_university_code + '.')) & (universities2['Code'].str.count('\.')== 1)]['Department'].tolist(), index=0
                        ) # Institut
                        if selected_institute != "All":
                            selected_institute_code = universities2[universities2['Department'] == selected_institute]['Code'].values[0]
                            selected_department = right.selectbox('Department:', 
                            ["All"] + universities2[
                                (universities2['Code'].str.startswith(selected_institute_code + '.')) & (universities2['Code'].str.count('\.') == 2)]['Department'].tolist(), index=0
                            ) # Avdelning
                            if selected_department != "All":
                                selected_department_code = universities2[universities2['Department'] == selected_department]['Code'].values[0]
                            else:
                                selected_department_code = ""
                        else:
                            selected_institute_code = ""
                    else:
                        selected_university_code = ""

                    if selected_university != "All":
                        if selected_institute != "All":
                            if selected_department != "All":
                                affiliation_search = f'{selected_university_code}.{selected_institute_code}.{selected_department_code}'
                            else:
                                affiliation_search = f'{selected_university_code}.{selected_institute_code}'
                        else: 
                            affiliation_search = f'{selected_university_code}'

                    if selected_university != "All":
                        df = df[
                            df[column].astype(str).str.startswith(affiliation_search) |
                            df[column].astype(str).str.contains(f';{affiliation_search}')
                        ]

                elif column == "Year":
                    year_range = right.slider('År:', min_value=1990, max_value=2024, value=(1990, 2024)) # År slider
                    fran_ar, till_ar = year_range
                    df = df.loc[df[column].between(fran_ar, till_ar)]

                elif is_categorical_dtype(df[column]) or df[column].nunique() < 50:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]

                else:
                    user_text_input = right.text_input(
                        f"Filter for {column} containing:",
                    )
                    if user_text_input:
                        df = df[df[column].astype(str).str.contains(user_text_input, case=False)]
        return df

    # Fetch data
    df = fetch_data_tidsskrift()

    # Filter the DataFrame
    filtered_df = filter_dataframe(df)

    st.write(' ')

    # Search button
    search_button = st.button('Search')

    st.write(' ')

    # Display matching results and journal counts
    if search_button:
        if not filtered_df.empty:
            # Group by journal and count the number of papers
            journal_counts = filtered_df['Journal'].value_counts().reset_index()
            journal_counts.index = journal_counts.index + 1
            journal_counts.columns = ['Journal', 'Total Papers']

            # Display the grouped DataFrame
            st.write(f"Number of results: {len(filtered_df)}")

            # Function to truncate journal names
            def truncate_journal_name(name, max_length=40):
                if len(name) > max_length:
                    return name[:max_length] + '...'
                return name

            # Apply truncation to the 'Journal' column
            journal_counts['Truncated Journal'] = journal_counts['Journal'].apply(truncate_journal_name)

            # Sort by "Total Papers" in descending order and select the top 10
            top_journals = journal_counts.sort_values(by="Total Papers", ascending=False).head(15)

            top_journals = top_journals.sort_values(by='Total Papers', ascending=True)

            # Horizontal bar plot
            if not top_journals.empty:
                fig1 = px.bar(top_journals, x='Total Papers', y='Truncated Journal', title='Total Papers Published in Each Journal',
                            labels={'Journal': 'Journal', 'Total Papers': 'Number of Papers'}, orientation='h')
                fig1.update_layout(width=2000, height=800)
                st.plotly_chart(fig1)
                
                st.dataframe(journal_counts.head(50), width=1200, height=400)
                st.write('---')

                # Check if 'fig' is defined and is an instance of a Plotly figure
                if fig1 is not None:
                    # Save the figure to a PDF buffer
                    pdf_buffer = io.BytesIO()
                    fig1.write_image(pdf_buffer, format='pdf')

                    # Reset the buffer position to the beginning
                    pdf_buffer.seek(0)

                    # Add a button to download the figure as a PDF
                    st.download_button(
                        label="Download Total Papers Published in Each Journal as PDF",
                        data=pdf_buffer,
                        file_name="vetu_figure.pdf",
                        mime="application/pdf",
                        key="journal_fig1"
                    )

        else:
            st.write("No matching results found.")
            st.write('---')
    else:
        st.write('Please select filters.')