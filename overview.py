## Översikt

import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import plotly.express as px
from supabase import create_client, Client
import plotly.io as pio

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

# Get all the data
def fetch_overview_data():
    conn = create_conn()
    citation_impact_query = "SELECT citations, year, impactful_citations FROM vetu_paper"
    author_query = "SELECT name FROM vetu_author"
    
    citation_impact_df = pd.read_sql_query(citation_impact_query, conn)
    author_df = pd.read_sql_query(author_query, conn)
    conn.close()

    citation_columns = ['year', 'citations']
    impact_columns = ['citations', 'year', 'impactful_citations']
    
    citation_df = citation_impact_df[citation_columns]
    impact_df = citation_impact_df[impact_columns]

    # Calculate totals
    total_citations = impact_df['citations'].sum()
    total_impactful_citations = impact_df['impactful_citations'].sum()
    total_papers = impact_df['citations'].count()
    total_authors = author_df['name'].nunique()

    # Categorize papers based on citation counts
    citation_df['citation_category'] = pd.cut(
        citation_df['citations'],
        bins=[-1, 5, 10, citation_df['citations'].max()],
        labels=['≤5 Citations', '6-10 Citations', '>10 Citations']
    )

    # Calculate citation statistics
    percentage_papers_cited_6_through_10 = citation_df[citation_df['citation_category'].isin(['≤5 Citations', '6-10 Citations'])].shape[0]
    percentage_papers_cited_6_through_10 = round(percentage_papers_cited_6_through_10 * 100 / total_papers, 2)

    total_papers_cited_5_or_less = citation_df[citation_df['citation_category'].isin(['≤5 Citations'])].shape[0]
    percentage_papers_cited_5_or_less = round(total_papers_cited_5_or_less * 100 / total_papers, 2)

    percentage_papers_cited_more_than_10 = round(100 - percentage_papers_cited_6_through_10 - percentage_papers_cited_5_or_less, 2)

    # Prepare the impact data for plotting
    impact_df = impact_df.rename(columns={
        "year": "Year",
        "citations": "Total Citations",
        "impactful_citations": "Impactful Citations",
    }).groupby('Year').sum().reset_index()

    return total_citations, total_papers, total_authors, percentage_papers_cited_more_than_10, percentage_papers_cited_6_through_10, percentage_papers_cited_5_or_less, citation_df, impact_df

def plot_papers_per_year():
    conn = create_conn()
    query = "SELECT year FROM vetu_paper"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Group by year and count the number of papers
    papers_per_year = df['year'].value_counts().reset_index()
    papers_per_year.columns = ['Year', 'Total Papers']
    papers_per_year = papers_per_year.sort_values('Year')
    
    return papers_per_year

    fig = px.bar(
        papers_per_year, 
        x='Year', 
        y='Total Papers', 
        title='Total Papers Published Each Year',
        labels={'Year': 'Year', 'Total Papers': 'Number of Papers'}
        )
    
    # Update the x-axis range to start at 1990
    fig.update_layout(
        xaxis=dict(
            range=[1989, 2025],
            tickmode='linear',
            tick0=1990,
            dtick=5
        )
    )
    return fig

def calculate_percentage_composition_citations(citation_df):
    # Calculate the percentage composition for each year
    composition_df = citation_df.groupby(['year', 'citation_category']).size().reset_index(name='count')
    total_per_year = composition_df.groupby('year')['count'].transform('sum')
    composition_df['percentage'] = composition_df['count'] / total_per_year * 100

    # Pivot the data for plotting
    pivot_df = composition_df.pivot(index='year', columns='citation_category', values='percentage').fillna(0)

    return pivot_df

def bar_plot_citation_composition(pivot_df):
    # Define custom colors
    custom_colors = ['#F60909', '#FFF710', '#11C618']  # Red, yellow, green
    # Plot the percentage composition as a stacked bar chart
    fig = px.bar(
        pivot_df, 
        x=pivot_df.index, 
        y=pivot_df.columns, 
        title='Percentage of Papers by Citation Counts (1990-2024)',
        labels={'value': 'Percentage', 'year': 'Year'}, 
        barmode='stack', 
        color_discrete_sequence=custom_colors
    )

    # Update the x-axis range to start at 1990
    fig.update_layout(
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
    return fig

def bar_plot_total_citations(impact_df):
    fig = px.bar(
        impact_df, 
        x='Year', 
        y='Total Citations', 
        title='Total Papers Cited Each Year',
        labels={'Year': 'Year', 'Total Citations': 'Total Citations'}
    )

    # Update the x-axis range to start at 1990
    fig.update_layout(
        xaxis=dict(
            range=[1989, 2025],
            tickmode='linear',
            tick0=1990,
            dtick=5
        )
    )
    return fig