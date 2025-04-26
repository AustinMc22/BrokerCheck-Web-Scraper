import streamlit as st
import pandas as pd
import math

st.set_page_config(layout="wide")
st.title("BrokerCheck Active Brokers")

@st.cache_data
def load_data():
    df = pd.read_feather("all_brokers_output.feather")
    
    # Ensure proper links without double quotes
    df["BrokerCheck Profile URL"] = df["BrokerCheck Profile URL"].apply(
        lambda url: f'<a href={url.strip("\"")} target="_blank">{url.strip("\"")}</a>'
    )
    
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filter Options")
filter_columns = [
    "BrokerCheck Profile URL", "CRD#", "Full name", "City", "State", "Zip code",
    "Current Firms", "Previous Firms", "Year First Registered",
    "Licenses", "Disclosures", "Registration Type"
]
filters = {col: st.sidebar.text_input(f"{col} contains:", "") for col in filter_columns}

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
    page_number = st.sidebar.number_input("Page #", min_value=1, max_value=total_pages, value=1, step=1)

    start_idx = (page_number - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx]

    st.markdown(f"### Showing {len(filtered_df):,} of {len(df):,} broker profiles")
    st.markdown(paginated_df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.markdown("### No results found. Try adjusting your filters.")

# Test - nothing related to above