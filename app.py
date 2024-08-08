# Import necessary libraries
import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import plotly.express as px
from supabase import create_client, Client
import plotly.io as pio
import io
from pathlib import Path

# Configure the Streamlit page
st.set_page_config(layout="wide", page_title="VETU", page_icon=":chart_with_upwards_trend:", initial_sidebar_state="expanded")

#00A3FF
# Custom CSS to create a banner, ensure it's in front of the sidebar, and style the radio buttons
st.markdown("""
    <style>
    /* Banner styling */
    .banner {
        background-color: #468499; /* Change this to your desired background color */
        padding: 15px;
        padding-left: 30px;
        text-align: center;
        color: white;
        font-size: 1.75vw; /* Use viewport width for font size */
        font-weight: 600;
        font-family: 'Gill Sans', sans-serif; /* Change the font */
        position: fixed;
        top: 0;
        right: 0;
        width: 100%;
        z-index: 1000; /* Ensure the banner is in front of other elements */
    }

    /* Adjust the padding of the main content to account for the banner */
    .main .block-container {
        padding-top: 80px; /* Adjust this value if necessary to avoid overlap with banner */
    }

    /* Ensure sidebar is not affected */
    section[data-testid="stSidebar"] {
        z-index: 1; /* Ensure sidebar is behind the banner */
    }

    /* Radio button styling */
    div.stRadio > div {
        display: flex;
        flex-direction: column; /* Arrange the radio buttons in a column */
    }

    div.stRadio > div > label {
        display: block;
        padding: 10px 0;
        cursor: pointer;
        text-decoration: none; /* Remove underline */
        color: #007bff; /* Link color */
        font-weight: bold;
        font-size: 4vw; /* Use viewport width for font size */
        font-family: 'Futura', sans-serif; /* Change the font */
    }

    div.stRadio > div > label > input {
        display: none; /* Hide the radio input */
    }

    div.stRadio > div > label > div:nth-of-type(1) {
        display: none; /* Hide the default radio button */
    }

    /* Media query for smaller screens */
    @media (max-width: 600px) {
        .banner {
            padding: 10px;
            font-size: 8vw; /* Increase font size for smaller screens */
        }
        .main .block-container {
            padding-top: 60px; /* Adjust padding for smaller screens */
        }
        div.stRadio > div > label {
            font-size: 6vw; /* Adjust radio button font size for smaller screens */
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Banner with title
st.markdown('<div class="banner">VETU - Medicinsk Forskning</div>', unsafe_allow_html=True)

# Custom CSS to make the search button wider
st.markdown("""
    <style>
    .stButton button {
        width: 200px; /* Adjust the width as needed */
    }
    </style>
    """, unsafe_allow_html=True)

#Remove top streamlit banner
st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

# Set the default template for Plotly
pio.templates.default = "ggplot2"

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

# Create a sidebar with a header
st.sidebar.header(' ')
st.sidebar.header(' ')
st.sidebar.header('Välj verktyg')

# Navigation menu with options
navigation = st.sidebar.radio('', ('Översikt', 'Akademi & Högskola', 'Region (ALF)', 'Tidsskrifter', 'Forskare', 'Finansiärer', 'Innovation', 'Sök Artiklar'))

# Display the selected navigation title
st.write(' ')
st.title(navigation)
st.write('---')


if navigation == 'Översikt':

    # Get all the data
    def fetch_impact_citation_data():
            conn = create_conn()
            citation_impact_query = "SELECT citations, year, impactful_citations FROM vetu_paper"
            author_query = "SELECT name FROM vetu_author"
            
            citation_impact_df = pd.read_sql_query(citation_impact_query, conn)
            author_df = pd.read_sql_query(author_query, conn)

            citation_columns = ['year', 'citations']
            impact_columns = ['citations', 'year', 'impactful_citations']
            
            citation_df = citation_impact_df[citation_columns]
            impact_df = citation_impact_df[impact_columns]


            conn.close()
            return impact_df, citation_df, author_df
    
    # Create two columns for the layout
    col1, col2 = st.columns(2)

    # Column 1: Impact Summary
    with col1:

        # Fetch data
        impact_df, citation_df, impact_df_author = fetch_impact_citation_data()

        # Calculate totals
        total_citations = impact_df['citations'].sum()
        total_impactful_citations = impact_df['impactful_citations'].sum()
        total_papers = impact_df['citations'].count()
        total_authors = impact_df_author['name'].nunique()

        # Categorize papers based on citation counts
        citation_df['citation_category'] = pd.cut(
            citation_df['citations'],
            bins=[-1, 5, 10, citation_df['citations'].max()],
            labels=['≤5 Citations', '6-10 Citations', '>10 Citations']
        )

        # Calculate citation statistics
        total_papers_cited_10_or_less = citation_df[citation_df['citation_category'].isin(['≤5 Citations', '6-10 Citations'])].shape[0]
        percentage_papers_cited_10_or_less = round(total_papers_cited_10_or_less * 100 / total_papers, 2)

        total_papers_cited_5_or_less = citation_df[citation_df['citation_category'].isin(['≤5 Citations'])].shape[0]
        percentage_papers_cited_5_or_less = round(total_papers_cited_5_or_less * 100 / total_papers, 2)

        percentage_papers_cited_more_than_10 = round(100 - percentage_papers_cited_10_or_less - percentage_papers_cited_5_or_less, 2)

        # Display the info box
        st.markdown(f"""
        <div style="background-color: #d9d9d9; padding: 20px; border-radius: 15px;">
            <h3 style="color: #333;">Impact Summary</h3>
            <p><strong>Total Citations:</strong> {total_citations}</p>
            <p><strong>Total Number of Papers:</strong> {total_papers}</p>
            <p><strong>Total Number of Authors:</strong> {total_authors}</p>
            <p><strong>Percentage of Papers with >10 citations:</strong> {percentage_papers_cited_more_than_10}%</p>
            <p><strong>Percentage of Papers with 6-10 citations:</strong> {percentage_papers_cited_10_or_less}%</p>
            <p><strong>Percentage of Papers with ≤5 citations:</strong> {percentage_papers_cited_5_or_less}%</p>
        </div>
        """, unsafe_allow_html=True)

        # Add a separator
        st.write('---')

    # Column 2: Papers Published Each Year
    with col2:
        def fetch_papers_per_year():
            conn = create_conn()
            query = "SELECT year FROM vetu_paper"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df

        # Fetch data
        df = fetch_papers_per_year()

        # Group by year and count the number of papers
        papers_per_year = df['year'].value_counts().reset_index()
        papers_per_year.columns = ['Year', 'Total Papers']
        papers_per_year = papers_per_year.sort_values('Year')

        # Plot the bar chart for total papers published each year
        fig1 = px.bar(
            papers_per_year, 
            x='Year', 
            y='Total Papers', 
            title='Total Papers Published Each Year',
            labels={'Year': 'Year', 'Total Papers': 'Number of Papers'}
        )
        
        # Update the x-axis range to start at 1990
        fig1.update_layout(
            xaxis=dict(
                range=[1989, 2025],
                tickmode='linear',
                tick0=1990,
                dtick=5
            )
        )

        # Display the plot in Streamlit
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
                key="oversikt_fig1"
            )

    # Calculate the percentage composition for each year
    composition_df = citation_df.groupby(['year', 'citation_category']).size().reset_index(name='count')
    total_per_year = composition_df.groupby('year')['count'].transform('sum')
    composition_df['percentage'] = composition_df['count'] / total_per_year * 100

    # Pivot the data for plotting
    pivot_df = composition_df.pivot(index='year', columns='citation_category', values='percentage').fillna(0)

    # Define custom colors
    custom_colors = ['#F60909', '#FFF710', '#11C618']  # Red, yellow, green

    # Plot the percentage composition as a stacked bar chart
    fig2 = px.bar(
        pivot_df, 
        x=pivot_df.index, 
        y=pivot_df.columns, 
        title='Percentage of Papers by Citation Counts (1990-2024)',
        labels={'value': 'Percentage', 'year': 'Year'}, 
        barmode='stack', 
        color_discrete_sequence=custom_colors
    )

    # Update the x-axis range to start at 1990
    fig2.update_layout(
        xaxis=dict(
            range=[1990, 2025],
            tickmode='linear',
            tick0=1990,
            dtick=1
        ),
        yaxis=dict(
            title='Percentage'
        ),
        legend_title_text='Citation Groups'
    )

    # Display the plot in Streamlit
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
            key="oversikt_fig2"
        )

    # Prepare the impact data for plotting
    impact_df = impact_df.rename(columns={
        "year": "Year",
        "citations": "Total Citations",
        "impactful_citations": "Impactful Citations",
    }).groupby('Year').sum().reset_index()

    # Plot the bar chart for total citations each year
    fig3 = px.bar(
        impact_df, 
        x='Year', 
        y='Total Citations', 
        title='Total Papers Cited Each Year',
        labels={'Year': 'Year', 'Total Citations': 'Total Citations'}
    )

    # Update the x-axis range to start at 1990
    fig3.update_layout(
        xaxis=dict(
            range=[1989, 2025],
            tickmode='linear',
            tick0=1990,
            dtick=5
        )
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig3)

    # Check if 'fig' is defined and is an instance of a Plotly figure
    if fig3 is not None:
        # Save the figure to a PDF buffer
        pdf_buffer = io.BytesIO()
        fig3.write_image(pdf_buffer, format='pdf')

        # Reset the buffer position to the beginning
        pdf_buffer.seek(0)

        # Add a button to download the figure as a PDF
        st.download_button(
            label="Download as PDF",
            data=pdf_buffer,
            file_name="vetu_figure.pdf",
            mime="application/pdf",
            key="oversikt_fig3"
        )


elif navigation == 'Akademi & Högskola':

    # Function to fetch data from the database based on filters
    #### Tillfällig filter för titel istället för topic
    def fetch_data(university, institute, department, topic_filter, type_filter, from_year, to_year):
        conditions = []
        if university != "All":
            conditions.append(f"affiliations LIKE '%{university}%'")
        if institute != "All":
            conditions.append(f"affiliations LIKE '%{institute}%'")
        if department != "All":
            conditions.append(f"affiliations LIKE '%{department}%'")
        if topic_filter != "":
            topics = topic_filter.split(',')
            topic_conditions = [f"title LIKE '%{topic.strip()}%'" for topic in topics]
            conditions.append(f"({' OR '.join(topic_conditions)})")
        if type_filter != "":
            conditions.append(f"publication_type LIKE '%{type_filter}%'")
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

    # Create a box containing four dropdown menus
    with st.container():
        # Generate a list of years from 1990 to 2024
        fran_ar_list = list(range(1990, 2025))
        fran_ar = 1990

        # Arrange dropdown menus in columns
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        col5, col6, col7 = st.columns(3)
        col8, col9 = st.columns(2)
        col10, col11, col12 = st.columns(3)

        # Other dropdown menus
        with col1:
            year_range = st.slider('År:', min_value=1990, max_value=2024, value=(1990, 2024)) # År slider
            fran_ar, till_ar = year_range

        with col2:
            st.write("")
            st.write("")
            ytterliggare_filter = st.checkbox('Lägg till fler filter:')
            if ytterliggare_filter:
                with col3:
                    user_type_input = st.selectbox(
                        f"Select article type",
                        options=["All", "Case Reports", "Journal Article", "Clinical Trial", "Evaluation Study", "Randomized Controlled Trial", "Observational Study", "Systematic Review", "Meta-Analysis"],
                    )
                    if user_type_input:
                        if user_type_input == "All":
                            type_filter = ""
                        else:
                            type_filter = user_type_input
                    else:
                        type_filter = ""
                with col4:
                    user_title_input = st.text_input(
                        f"Filter for Topic containing:",
                    )
                    if user_title_input:
                        title_filter = user_title_input
                    else:
                        title_filter = ""
            else: 
                type_filter = ""
                title_filter = ""

        with col5:
            selected_university = st.selectbox('Universitet:', ["All"] + universities2[universities2['Code'].str.count('\.') == 0]['Department'].tolist(), index=0) # Universitet
            if selected_university != "All":
                selected_university_code = universities2[universities2['Department'] == selected_university]['Code'].values[0]
            else:
                selected_university_code = ""

        with col6:
            if selected_university == "ALL":
                st.selectbox('Institut:', ["All"])
            else:
                selected_institute = st.selectbox('Institut:',
                ["All"] + universities2[
                    (universities2['Code'].str.startswith(selected_university_code + '.')) & (universities2['Code'].str.count('\.')== 1)]['Department'].tolist(), index=0
                ) # Institut
                if selected_institute != "All":
                    selected_institute_code = universities2[universities2['Department'] == selected_institute]['Code'].values[0]
                else:
                    selected_institute_code = ""

        with col7:    
            if selected_institute == "ALL":
                st.selectbox('Department:', ["All"])
            else:
                selected_department = st.selectbox('Department:', 
                ["All"] + universities2[
                    (universities2['Code'].str.startswith(selected_institute_code + '.')) & (universities2['Code'].str.count('\.') == 2)]['Department'].tolist(), index=0
                ) # Avdelning

        with col8:
            jamfor_box = st.checkbox('Jämför')
            if jamfor_box:
                with col10:
                    selected_university_comp = st.selectbox('Jämför med Universitet:', ["All"] + universities2[universities2['Code'].str.count('\.') == 0]['Department'].tolist(), index=0) # Universitet
                    if selected_university_comp != "All":
                        selected_university_code_comp = universities2[universities2['Department'] == selected_university_comp]['Code'].values[0]
                    else:
                        selected_university_code_comp = ""

                with col11:
                    if selected_university_comp == "ALL":
                        st.selectbox('Institut:', ["All"])
                    else:
                        selected_institute_comp = st.selectbox('Jämför med Institut:',
                        ["All"] + universities2[
                            (universities2['Code'].str.startswith(selected_university_code_comp + '.')) & (universities2['Code'].str.count('\.')== 1)]['Department'].tolist(), index=0
                        ) # Institut
                        if selected_institute_comp != "All":
                            selected_institute_code_comp = universities2[universities2['Department'] == selected_institute_comp]['Code'].values[0]
                        else:
                            selected_institute_code_comp = ""

                with col12:    
                    if selected_institute_comp == "ALL":
                        st.selectbox('Department:', ["All"])
                    else:
                        selected_department_comp = st.selectbox('Jämför med Department:', 
                        ["All"] + universities2[
                            (universities2['Code'].str.startswith(selected_institute_code_comp + '.')) & (universities2['Code'].str.count('\.') == 2)]['Department'].tolist(), index=0
                        ) # Avdelning
                
                data2 = fetch_data(selected_university_comp, selected_institute_comp, selected_department_comp, title_filter, type_filter, fran_ar, till_ar)

            else:
                selected_university_comp = ""
                selected_institute_comp = ""
                selected_department_comp = ""
                data2 = pd.DataFrame()
        
        with col9:
            pass          


    # Fetch the data
    data = fetch_data(selected_university, selected_institute, selected_department, title_filter, type_filter, fran_ar, till_ar)

    # Check if search 1 and search 2 are the same
    same_search = (
        selected_university == selected_university_comp and
        selected_institute == selected_institute_comp and
        selected_department == selected_department_comp
    )

    # Helper function to create search description for legend
    def create_search_description(university, institute, department):
        desc = []
        if university != "All":
            desc.append(university)
        if institute != "All":
            desc.append(institute)
        if department != "All":
            desc.append(department)
        return " - ".join(desc) if desc else "All"

    # Function to create the bar chart for publication count
    def create_publications_chart(data1, data2, title):
        search1_desc = create_search_description(selected_university, selected_institute, selected_department)
        search2_desc = create_search_description(selected_university_comp, selected_institute_comp, selected_department_comp)
        
        data1['Search'] = search1_desc if not same_search else 'Search'
        if not data2.empty and not same_search:
            data2['Search'] = search2_desc
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
            legend_title_text='Affiliation',
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        return fig

    # Function to create the bar chart for total citations
    def create_citations_chart(data1, data2, title):
        search1_desc = create_search_description(selected_university, selected_institute, selected_department)
        search2_desc = create_search_description(selected_university_comp, selected_institute_comp, selected_department_comp)
        
        data1['Search'] = search1_desc if not same_search else 'Search'
        if not data2.empty and not same_search:
            data2['Search'] = search2_desc
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
            legend_title_text='Affiliation',
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        return fig

    # Function to create the bar chart for average citations per paper
    def create_avg_citations_chart(data1, data2, title):
        search1_desc = create_search_description(selected_university, selected_institute, selected_department)
        search2_desc = create_search_description(selected_university_comp, selected_institute_comp, selected_department_comp)
        
        data1['Search'] = search1_desc if not same_search else 'Search'
        if not data2.empty and not same_search:
            data2['Search'] = search2_desc
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
            legend_title_text='Affiliation',
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        return fig

    # Display the publication count chart
    if not data.empty:
        fig1 = create_publications_chart(data, data2, 'Publications Over Time')
        st.plotly_chart(fig1)

    # Display the total citations chart
    if not data.empty:
        fig2 = create_citations_chart(data, data2, 'Total Citations Over Time')
        st.plotly_chart(fig2)

    # Display the average citations per paper chart
    if not data.empty:
        fig3 = create_avg_citations_chart(data, data2, 'Average Citations per Paper Over Time')
        st.plotly_chart(fig3)

    # Add download buttons for the charts
    if not data.empty:
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

elif navigation == 'Region (ALF)':
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
                f"Filter for Topic containing:",
            )
            topic_filter = user_title_input if user_title_input else ""

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

    # Fetch the data based on the search terms
    if search_text:
        data1 = fetch_affiliations(search_text, type_filter, title_filter, major_code, specialty_code, fran_ar, till_ar)
        if search_text_2:
            data2 = fetch_affiliations(search_text_2, type_filter, title_filter, major_code, specialty_code, fran_ar, till_ar)
        else:
            data2 = pd.DataFrame()

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

elif navigation == 'Tidsskrifter':

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

                # elif is_numeric_dtype(df[column]):
                #     _min = float(df[column].min())
                #     _max = float(df[column].max())
                #     step = (_max - _min) / 100
                #     user_num_input = right.slider(
                #         f"Values for {column}",
                #         min_value=_min,
                #         max_value=_max,
                #         value=(_min, _max),
                #         step=step,
                #     )
                #     df = df[df[column].between(*user_num_input)]

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
            st.dataframe(journal_counts.head(50), width=1200, height=400)

            # Function to truncate journal names
            def truncate_journal_name(name, max_length=40):
                if len(name) > max_length:
                    return name[:max_length] + '...'
                return name

            # Apply truncation to the 'Journal' column
            journal_counts['Truncated Journal'] = journal_counts['Journal'].apply(truncate_journal_name)

            # Sort by "Total Papers" in descending order and select the top 10
            top_journals = journal_counts.sort_values(by="Total Papers", ascending=False).head(10)

            # Example plot (optional)
            if not top_journals.empty:
                fig1 = px.bar(top_journals, x='Truncated Journal', y='Total Papers', title='Total Papers Published in Each Journal',
                            labels={'Journal': 'Journal', 'Total Papers': 'Number of Papers'})
                fig1.update_layout(width=2000, height=600)
                st.plotly_chart(fig1)
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
                        label="Download as PDF",
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


    # st.write("---")
    # st.subheader('Top journals overall')
    # st.write(' ')

    # # Group by journal and count the number of papers
    # df_counts = df['Journal'].value_counts().reset_index()
    # df_counts.index = df_counts.index + 1
    # df_counts.columns = ['Journal', 'Total Papers']

    # # Apply truncation to the 'Journal' column
    # st.dataframe(df_counts, width=1200, height=800)

elif navigation == 'Forskare':

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
  
elif navigation == 'Finansiärer':
    st.write('Funktionen kommer snart')

elif navigation == 'Innovation':
    st.write('Funktionen kommer snart')

elif navigation == 'Sök Artiklar':

    from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
    )
    #import sqlite3

    def fetch_author_paper_data():
        conn = create_conn()
        query = "SELECT title, publication_type, abstract_text, journal_title, affiliations, pmid FROM vetu_paper"
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
            to_filter_columns = st.multiselect("Filter articles based on", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                if column == "Type of paper":
                    user_type_input = right.selectbox(
                        f"Select {column}",
                        options=df[column].unique(),
                    )
                    df = df[df[column] == user_type_input]
                else:
                    user_text_input = right.text_input(
                        f"Filter for {column} containing:",
                    )
                    if user_text_input:
                        df = df[df[column].astype(str).str.contains(user_text_input, case=False)]
        return df

    # Fetch data
    author_paper_df = fetch_author_paper_data()

    # Filter the DataFrame
    filtered_df = filter_dataframe(author_paper_df)

    search_button = st.button('Search')

    st.write('---')

    # Display matching results
    if search_button:
        if not filtered_df.empty:
            st.text(f"{len(filtered_df)} results")
            top_50_df = filtered_df.head(50)
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


