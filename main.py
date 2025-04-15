import requests
import xml.etree.ElementTree as ET

print("FINRA RIA Scraper ready to go!")

# Download the sitemap
sitemap_url = "https://files.brokercheck.finra.org/sitemap.xml"
response = requests.get(sitemap_url)

# Parse the XML
root = ET.fromstring(response.content)

# Open a new text file to save the links
with open("output.txt", "w") as file:
    # Loop through the XML and print out the broker profile links
    for child in root:
        for url in child:
            if url.text:  # Only print if it has text inside
                print(url.text)  # Still print to terminal
                file.write(url.text + "\n")  # Write to file

# Open the output file containing sitemap links
with open("output.txt", "r") as file:
    sitemap_links = file.readlines()

# Open a new file to store broker profile links
with open("broker-urls.txt", "w") as broker_file:
    for sitemap in sitemap_links:
        sitemap = sitemap.strip()  # Remove newline character
        response = requests.get(sitemap)
        root = ET.fromstring(response.content)

        for child in root:
            for url in child:
                if url.text and "/individual/summary/" in url.text:
                    print(url.text)  # Print to terminal
                    broker_file.write(url.text + "\n")  # Write to file






