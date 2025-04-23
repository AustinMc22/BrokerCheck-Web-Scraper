import aiohttp
import asyncio
import csv
import os
from PyPDF2 import PdfReader
from tqdm import tqdm
from clean_broker_sample import (
    extract_text_from_pdf,
    extract_crd_from_filename,
    extract_name,
    extract_address,
    extract_current_firm,
    extract_previous_firms,
    extract_first_registration_year,
    extract_licenses,
    extract_disclosures,
    extract_registration_type,
)

# Config
CONCURRENCY = 35
OUTPUT_FILE = "all_brokers_output.csv"
HEADERS = [
    "BrokerCheck Profile URL",
    "CRD#",
    "Full name",
    "City",
    "State",
    "Zip code",
    "Current Firms",
    "Previous Firms",
    "Year First Registered",
    "Licenses",
    "Disclosures",
    "Registration Type"
]

# Load CRDs
def load_crd_list(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip().isdigit()]

# Download individual PDF
async def download_pdf(session, crd):
    url = f"https://files.brokercheck.finra.org/individual/individual_{crd}.pdf"
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                content = await resp.read()
                return crd, content
            else:
                return crd, None
    except Exception:
        return crd, None

# Parse PDF
def process_pdf(crd, pdf_bytes):
    try:
        from io import BytesIO
        text = extract_text_from_pdf(BytesIO(pdf_bytes))

        url = f'"https://brokercheck.finra.org/individual/summary/{crd}"'
        full_name = extract_name(text)
        city, state, zip_code = extract_address(text)
        current_firm = extract_current_firm(text)
        previous_firms = extract_previous_firms(text)
        registration_year = extract_first_registration_year(text)
        licenses = extract_licenses(text)
        disclosures = extract_disclosures(text)
        reg_type = extract_registration_type(text)

        return [
            url,
            crd,
            full_name,
            city,
            state,
            zip_code,
            current_firm,
            previous_firms,
            registration_year,
            licenses,
            disclosures,
            reg_type
        ]
    except Exception as e:
        return [f"https://brokercheck.finra.org/individual/summary/{crd}", crd] + ["Error"] * (len(HEADERS) - 2)

# Main async runner
async def main():
    crds = load_crd_list("all_crds_expected.txt")
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)

            async def fetch_and_process(crd):
                async with semaphore:
                    crd, pdf_bytes = await download_pdf(session, crd)
                    if pdf_bytes:
                        row = process_pdf(crd, pdf_bytes)
                    else:
                        row = [f"https://brokercheck.finra.org/individual/summary/{crd}", crd] + ["PDF Download Failed"] * (len(HEADERS) - 2)
                    writer.writerow(row)

            tasks = [fetch_and_process(crd) for crd in crds]
            for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                await f

if __name__ == "__main__":
    asyncio.run(main())