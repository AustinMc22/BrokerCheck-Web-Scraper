import pandas as pd

# Expand pandas display options
pd.set_option("display.max_columns", None)   # Show all columns
pd.set_option("display.max_colwidth", None)  # Show full text in each column
pd.set_option("display.width", 1000)         # Set a wide display width

# Load a sample of the CSV
df = pd.read_csv("all_brokers_output.csv", nrows=10)

# Print full sample
print(df.head())

# Optional: print all column names
print("\nColumns in the file:")
print(df.columns.tolist())
