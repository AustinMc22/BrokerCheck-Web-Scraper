import requests
import io
import csv
from PyPDF2 import PdfReader

with open("test-broker-urls.txt", "r") as f:
    urls = [line.strip() for line in f.readlines() if line.strip()]

with open("broker_data_output.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "CRD#", "Full name", "Full address", "City", "State", "Zip code",
        "Current Firms", "Previous Firm(s)", "Registration Year",
        "Licenses", "Exams Passed", "Disclosures Count",
        "Years all disclosures occurred", "currently inactive due to incomplete requirements"
    ])

    for url in urls:
        broker_id = url.split("/")[-1]
        pdf_url = f"https://files.brokercheck.finra.org/individual/individual_{broker_id}.pdf"

        try:
            response = requests.get(pdf_url)
            if response.status_code == 200:
                pdf_reader = PdfReader(io.BytesIO(response.content))
                full_text = ""

                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text

                full_text = full_text.replace("\n", " ").strip()
                
                print(full_text) # <-- Add this to see what is being scraped

                # Test values for now
                crd_number = ""
                full_name = ""
                full_address = ""
                city = ""
                state = ""
                zip_code = ""
                # Determine inactive status
                if "Inactive - Continuing Education" in full_text:
                    inactive_flag = "Yes"
                else:
                    inactive_flag = "No"



                writer.writerow([
                    crd_number,
                    full_name,
                    full_address,
                    city,
                    state,
                    zip_code,
                    "",  # Current Firms
                    "",  # Previous Firms
                    "",  # Registration Year
                    "",  # Licenses
                    "",  # Exams Passed
                    "",  # Disclosures Count
                    "",  # Disclosure Years
                    inactive_flag
                ])
            else:
                print(f"PDF not found for: {url}")

        except Exception as e:
            print(f"Error processing {url}: {e}")
