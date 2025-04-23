import pandas as pd

# Load just 5 rows from your broker CSV
df = pd.read_csv("all_brokers_output.csv", nrows=5)

# Reverse each broker's full name
df["Full name (Reversed)"] = df["Full name"].apply(lambda x: str(x)[::-1])

# Show the result
print(df[["CRD#", "Full name", "Full name (Reversed)"]])
