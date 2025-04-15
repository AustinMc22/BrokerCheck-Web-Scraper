import requests
import time
import io
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_broker(url):
    url = url.strip()
    broker_id = url.split("/")[-1]
    pdf_url = f"https://files.brokercheck.finra.org/individual/individual_{broker_id}.pdf"

    try:
        response = requests.get(pdf_url, timeout=10)

        if response.status_code == 200:
            pdf_reader = PdfReader(io.BytesIO(response.content))
            full_text = ""

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text

            full_text = full_text.replace("\n", " ").strip()

            if (
                "Currently employed by and registered with the following Firm(s):" in full_text
                and "This broker is not currently registered." not in full_text
            ):
                print(f"Active Broker Found: {url}")
                return url  # Return the URL if active

            else:
                print(f"Inactive Broker Skipped: {url}")
                return None  # Skip if inactive

        else:
            print(f"PDF not found for: {url}")
            return None

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None


with open("broker-urls.txt", "r") as file:
    urls = file.readlines()

# Write active brokers to file
with open("active-broker-urls.txt", "w") as active_file:
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_broker, url) for url in urls]

        for future in as_completed(futures):
            result = future.result()
            if result:
                active_file.write(result + "\n")
