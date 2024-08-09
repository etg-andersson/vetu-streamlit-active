## Översikt

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
