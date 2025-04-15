import requests
import time
import os
import io
from PyPDF2 import PdfReader  # Install with: pip install PyPDF2

# Read all broker profile URLs
with open("broker-urls.txt", "r") as file:
    urls = file.readlines()

# Create / open the file to store active brokers
with open("active-broker-urls.txt", "w") as active_file:
    for url in urls:
        url = url.strip()
        broker_id = url.split("/")[-1]
        pdf_url = f"https://files.brokercheck.finra.org/individual/individual_{broker_id}.pdf"

        try:
            response = requests.get(pdf_url)
            if response.status_code == 200:
                pdf_reader = PdfReader(io.BytesIO(response.content))

                full_text = ""
                for page in pdf_reader.pages:
                    full_text += page.extract_text()

                if "Registration Status: Active" in full_text:
                    print(f"Active Broker Found: {url}")
                    active_file.write(url + "\n")

            else:
                print(f"PDF not found for: {url}")

            time.sleep(0.5)  # Delay between requests to be polite

        except Exception as e:
            print(f"Error processing {url}: {e}")