import requests

# Extract the FINRA ID from the URL
finra_id = "1070942"

# This is the BrokerCheck API endpoint
api_url = f"https://api.brokercheck.finra.org/search/individual/{finra_id}?hl=true&includePrevious=true"

response = requests.get(api_url)
data = response.json()

# Print the full JSON response to explore what’s inside
print(data)

