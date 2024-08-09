import streamlit as st

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

    from overview import overview_view

    overview_view()

elif navigation == 'Akademi & Högskola':

    from universities import university_view

    university_view()

elif navigation == 'Region (ALF)':

    from regions import regions_view

    regions_view()

elif navigation == 'Tidsskrifter':

    from journals import journal_view

    journal_view()

elif navigation == 'Forskare':

    from researcher import researcher_view

    researcher_view()
  
elif navigation == 'Finansiärer':
    
    from funding import funding_view

    funding_view()

elif navigation == 'Innovation':
    
    from innovation import innovation_view

    innovation_view()

elif navigation == 'Sök Artiklar':

    from search import search_view

    search_view()
