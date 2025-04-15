import requests
import csv
import time

# Open the file with broker URLs
with open("broker-urls.txt", "r") as f:
    broker_urls = f.readlines()

# Open a CSV to store the data
with open("brokers.csv", "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    
    # Write your header row (field names)
    writer.writerow(["finra_id", "raw_data"])

    for url in broker_urls:
        url = url.strip()
        
        # Extract the FINRA ID from the URL
        finra_id = url.split("/")[-1]

        api_url = f"https://api.brokercheck.finra.org/search/individual/{finra_id}?hl=true&includePrevious=true"

        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            
            # Write the ID + full raw JSON to the CSV
            writer.writerow([finra_id, data])
        
        else:
            print(f"Failed to fetch broker {finra_id} — Status Code: {response.status_code}")

        # Be polite — wait 0.5 seconds between API calls so we don’t hammer their server
        time.sleep(0.5)
