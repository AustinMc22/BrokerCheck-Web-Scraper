import os
import requests

URL_FILE = "test-broker-urls.txt"
PDF_FOLDER = "sample_brokers"

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

with open(URL_FILE, "r") as file:
    urls = [line.strip() for line in file if line.strip()]

for url in urls:
    try:
        crd = url.split("/")[-1]
        pdf_url = f"https://files.brokercheck.finra.org/individual/individual_{crd}.pdf"
        pdf_path = os.path.join(PDF_FOLDER, f"individual_{crd}.pdf")

        response = requests.get(pdf_url)
        response.raise_for_status()

        with open(pdf_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Downloaded {pdf_path}")
    except Exception as e:
        print(f"❌ Failed to download {url} — {e}")
