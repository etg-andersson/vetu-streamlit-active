### Researcher

def researcher_view():

    import streamlit as st
    import pandas as pd
    import psycopg2
    import matplotlib.pyplot as plt
    import plotly.express as px
    from supabase import create_client, Client
    import plotly.io as pio
    import io
    from pathlib import Path

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

    # Function to fetch data from the database
    def fetch_data_forskare():
        conn = create_conn()
        query = """
        SELECT name, citations, impactful_citations, paper_count, affiliations 
        FROM vetu_authorimpact 
        WHERE EXISTS (
            SELECT 1 
            FROM unnest(affiliations) AS aff 
            WHERE aff LIKE '%Sweden%'
        )
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # Fetch data
    df_forskare = fetch_data_forskare()

    # Rename the columns
    df_forskare1 = df_forskare.rename(columns={
        "name": "Author",
        "citations": "Total Citations",
        "impactful_citations": "Impactful Citations",
        "paper_count": "Number of Papers",
        "affiliations": "Affiliation"
    })
    # Add a unique identifier for each row
    df_forskare1["Unique Author"] = df_forskare1["Author"] + " (" + df_forskare1.index.astype(str) + ")"


    df_forskare2 = df_forskare1

    # Reset the index and drop the original index
    df_forskare2 = df_forskare2.sort_values(by="Total Citations", ascending=False).head(50)
    df_forskare2 = df_forskare2.reset_index(drop=True)
    df_forskare2.index = df_forskare2.index + 1

    # Select relevant columns for display
    columns_to_display = ["Author", "Total Citations", "Impactful Citations", "Number of Papers", "Affiliation"]
    df_forskare2 = df_forskare2[columns_to_display]

    # First Subtitle
    st.subheader('Jämför forskare efter affiliation')

    # Create search bar
    search_query = st.text_input("Search within data", "")

    # Filter the DataFrame based on the search query

    if search_query:
        df_forskare_resultat = df_forskare2[df_forskare2.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
    else:
        df_forskare_resultat = df_forskare2

    # Display filtered DataFrame
    st.dataframe(df_forskare_resultat, width=1600, height=300)

    # Sort by "Total Citations" in descending order and select the top 10
    df_forskare_resultat2 = df_forskare_resultat.sort_values(by="Total Citations", ascending=False).head(20)

    # Example plot (optional)
    if not df_forskare_resultat2.empty:
        fig1 = px.bar(df_forskare_resultat2, x='Author', y='Total Citations', title='Citations by Author',
                    labels={'Unique Author': 'Author', 'Citations': 'Number of Citations'})
        st.plotly_chart(fig1)

        # Check if 'fig' is defined and is an instance of a Plotly figure
        if fig1 is not None:
            # Save the figure to a PDF buffer
            pdf_buffer = io.BytesIO()
            fig1.write_image(pdf_buffer, format='pdf')

            # Reset the buffer position to the beginning
            pdf_buffer.seek(0)

            # Add a button to download the figure as a PDF
            st.download_button(
                label="Download as PDF",
                data=pdf_buffer,
                file_name="vetu_figure.pdf",
                mime="application/pdf",
                key="author_fig1"
            )

    # Second Subtitle
    st.write('---')
    st.subheader('Jämför individuella forskare')

    # Allow users to select authors
    selected_authors = st.multiselect('Search authors to compare:', df_forskare1['Author'].unique())

    # Filter the DataFrame based on selected authors
    if selected_authors:
        selected_data = df_forskare1[df_forskare1['Author'].isin(selected_authors)]

        # Plot the selected data
        fig2 = px.bar(selected_data, x='Author', y='Total Citations', title='Total Citations by Selected Authors',
                    labels={'Author': 'Author', 'Total Citations': 'Number of Citations'})
        st.plotly_chart(fig2)

        # Check if 'fig' is defined and is an instance of a Plotly figure
        if fig2 is not None:
            # Save the figure to a PDF buffer
            pdf_buffer = io.BytesIO()
            fig2.write_image(pdf_buffer, format='pdf')

            # Reset the buffer position to the beginning
            pdf_buffer.seek(0)

            # Add a button to download the figure as a PDF
            st.download_button(
                label="Download as PDF",
                data=pdf_buffer,
                file_name="vetu_figure.pdf",
                mime="application/pdf",
                key="author_fig2"
            )
    else:
        st.write("No authors selected.")

    #Third subtitle
    st.write('---')
    st.subheader('Topplista efter antal citat')

    # Reset the index and drop the original index
    df_topplista = df_forskare1.sort_values(by="Total Citations", ascending=False).head(200)
    df_topplista = df_topplista.reset_index(drop=True)
    df_topplista.index = df_topplista.index + 1

    # Show topplista
    # Select relevant columns for display
    columns_to_display = ["Author", "Total Citations", "Impactful Citations", "Number of Papers", "Affiliation"]
    df_topplista = df_topplista[columns_to_display]

    # Display filtered DataFrame
    st.dataframe(df_topplista, width=1600, height=1600)


    # Create an empty portion of the page
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')
    st.write('  ')