import streamlit as st
import pandas as pd
import math

st.set_page_config(layout="wide")
st.title("FINRA BrokerCheck Explorer")

@st.cache_data
def load_data():
    df = pd.read_feather("all_brokers_output.feather")
    return df

# Load the data once
df = load_data()

# Sidebar Filters
st.sidebar.header("Filter Options")
filters = {
    "CRD#": st.sidebar.text_input("CRD# contains:"),
    "Full name": st.sidebar.text_input("Full name contains:"),
    "City": st.sidebar.text_input("City contains:"),
    "State": st.sidebar.text_input("State contains:"),
    "Zip code": st.sidebar.text_input("Zip code contains:"),
    "Current Firms": st.sidebar.text_input("Current Firms contains:"),
    "Previous Firms": st.sidebar.text_input("Previous Firms contains:"),
    "Year First Registered": st.sidebar.text_input("Year First Registered contains:"),
    "Licenses": st.sidebar.text_input("Licenses contains:"),
    "Disclosures": st.sidebar.text_input("Disclosures contains:"),
    "Registration Type": st.sidebar.text_input("Registration Type contains:")
}

# Apply filters
filtered_df = df.copy()
for col, val in filters.items():
    if val:
        filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, case=False, na=False)]

# Pagination
rows_per_page = 100
total_rows = len(filtered_df)

if total_rows > 0:
    total_pages = math.ceil(total_rows / rows_per_page)
    st.sidebar.markdown("---")
    page_number = st.sidebar.number_input(
        "Page #", min_value=1, max_value=total_pages, value=1, step=1
    )

    start_idx = (page_number - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx].copy()

    # Convert URLs to clickable links
    paginated_df["BrokerCheck Profile URL"] = paginated_df["BrokerCheck Profile URL"].apply(
        lambda url: f'<a href="{url}" target="_blank">Link</a>'
    )

    # Display
    st.markdown(f"### Showing {len(filtered_df):,} of {len(df):,} broker profiles")
    column_order = [
        "BrokerCheck Profile URL", "CRD#", "Full name", "City", "State", "Zip code",
        "Current Firms", "Previous Firms", "Year First Registered", "Licenses",
        "Disclosures", "Registration Type"
    ]
    st.markdown(paginated_df[column_order].to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.markdown("### No results found. Try adjusting your filters.")
