### University

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


# Generate a list of years from 1990 to 2024
fran_ar_list = list(range(1990, 2025))
fran_ar = 1990

# Arrange dropdown menus in columns
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col6 = st.columns(2)
col7, col8, col9 = st.columns(3)
col10, col11 = st.columns(2)
col12, col13, col14 = st.columns(3)

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
                f"Filter for Title containing:",
            )
            if user_title_input:
                title_filter = user_title_input
            else:
                title_filter = ""
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
        type_filter = ""
        title_filter = ""
        major_code = "All"
        specialty_code = "All"

with col7:
    selected_university = st.selectbox('Universitet:', ["All"] + universities2[universities2['Code'].str.count('\.') == 0]['Department'].tolist(), index=0) # Universitet
    if selected_university != "All":
        selected_university_code = universities2[universities2['Department'] == selected_university]['Code'].values[0]
    else:
        selected_university_code = ""

with col8:
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

with col9:    
    if selected_institute == "ALL":
        st.selectbox('Department:', ["All"])
    else:
        selected_department = st.selectbox('Department:', 
        ["All"] + universities2[
            (universities2['Code'].str.startswith(selected_institute_code + '.')) & (universities2['Code'].str.count('\.') == 2)]['Department'].tolist(), index=0
        ) # Avdelning

with col10:
    jamfor_box = st.checkbox('Jämför')
    if jamfor_box:
        with col12:
            selected_university_comp = st.selectbox('Jämför med Universitet:', ["All"] + universities2[universities2['Code'].str.count('\.') == 0]['Department'].tolist(), index=0) # Universitet
            if selected_university_comp != "All":
                selected_university_code_comp = universities2[universities2['Department'] == selected_university_comp]['Code'].values[0]
            else:
                selected_university_code_comp = ""

        with col13:
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

        with col14:    
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

with col11:
    pass          

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

# Initialize session state for figures
if 'fig1' not in st.session_state:
    st.session_state['fig1'] = None
if 'fig2' not in st.session_state:
    st.session_state['fig2'] = None
if 'fig3' not in st.session_state:
    st.session_state['fig3'] = None

# Define search button
search_button = st.button("Search")

# Check if the search button was pressed
if search_button:
    # Fetch the data
    data = fetch_data(selected_university, selected_institute, selected_department, title_filter, type_filter, fran_ar, till_ar)

    # Check if search 1 and search 2 are the same
    same_search = (
        selected_university == selected_university_comp and
        selected_institute == selected_institute_comp and
        selected_department == selected_department_comp
    )

    # Display the publication count chart
    if not data.empty or not data2.empty:
        if data.empty:
            st.write("No data available for the first selection.")
        elif data2.empty:
            if jamfor_box:
                st.write("No data available for second selection.")
            else:
                pass

        st.session_state['fig1'] = create_publications_chart(data, data2, 'Publications Over Time')
        st.session_state['fig2'] = create_citations_chart(data, data2, 'Total Citations Over Time')
        st.session_state['fig3'] = create_avg_citations_chart(data, data2, 'Average Citations per Paper Over Time')
        
    else:
        st.session_state['fig1'] = None
        st.session_state['fig2'] = None
        st.session_state['fig3'] = None
        st.write("No data available for the given filters and year range.")

# Display the charts if they exist
if st.session_state['fig1'] is not None:
    st.plotly_chart(st.session_state['fig1'])
    st.plotly_chart(st.session_state['fig2'])
    st.plotly_chart(st.session_state['fig3'])

    # Add download buttons
    pdf_buffer1 = io.BytesIO()
    st.session_state['fig1'].write_image(pdf_buffer1, format='pdf')
    pdf_buffer1.seek(0)
    st.download_button(
        label="Download publications chart as PDF",
        data=pdf_buffer1,
        file_name="publications_chart.pdf",
        mime="application/pdf"
    )
    
    pdf_buffer2 = io.BytesIO()
    st.session_state['fig2'].write_image(pdf_buffer2, format='pdf')
    pdf_buffer2.seek(0)
    st.download_button(
        label="Download total citations chart as PDF",
        data=pdf_buffer2,
        file_name="citations_chart.pdf",
        mime="application/pdf"
    )

    pdf_buffer3 = io.BytesIO()
    st.session_state['fig3'].write_image(pdf_buffer3, format='pdf')
    pdf_buffer3.seek(0)
    st.download_button(
        label="Download average citations per paper chart as PDF",
        data=pdf_buffer3,
        file_name="avg_citations_chart.pdf",
        mime="application/pdf"
    )
else:
    st.write("Please select filters.")