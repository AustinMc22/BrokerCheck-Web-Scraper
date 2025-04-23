import streamlit as st
import pandas as pd
import math

st.set_page_config(layout="wide")
st.title("FINRA BrokerCheck Explorer")

# Load and cache the data
@st.cache_data
def load_data():
    # Replace with your feather file path
    df = pd.read_feather("all_brokers_output.feather")
    return df

with st.spinner("Loading data..."):
    df = load_data()

# Sidebar Filters (limited to key columns for speed)
st.sidebar.header("Filter Options")
filter_cols = ["City", "State", "Current Firms", "Licenses"]
filters = {}
for col in filter_cols:
    if col in df.columns:
        filters[col] = st.sidebar.text_input(f"{col} contains:", "")

# Apply filters
filtered_df = df.copy()
for col, val in filters.items():
    if val:
        filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, case=False, na=False)]

# Pagination + Display
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
    paginated_df = filtered_df.iloc[start_idx:end_idx]

    st.markdown(f"### Showing {len(filtered_df):,} of {len(df):,} broker profiles")
    st.dataframe(paginated_df)
else:
    st.markdown("### No results found. Try adjusting your filters.")