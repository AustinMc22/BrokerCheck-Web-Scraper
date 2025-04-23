import aiohttp
import asyncio
import csv
import io
import os
from PyPDF2 import PdfReader
from tqdm import tqdm
import re

# Output CSV path
OUTPUT_FILE = "missing_brokers_output.csv"
CONCURRENCY = 25  # Number of concurrent requests

# List of fields
HEADERS = [
    "CRD#",
    "Full name",
    "Full address",
    "City",
    "State",
    "Zip code",
    "Current Firms",
    "Previous Firm(s)",
    "Registration Year",
    "Licenses",
    "Exams Passed",
    "Disclosures Count",
    "Disclosure Years",
    "Inactive - Continuing Education",
    "Registration Type",
    "Exam Filter"
]

# Extract helper functions
def extract_field(text, label):
    match = re.search(fr"{label}\s*[:\-]?\s*(.+?)(?=\s*[A-Z][a-z]+\s*:|$)", text)
    return match.group(1).strip() if match else "Not found"

def extract_license_numbers(text):
    matches = re.findall(r"(Series\s*)?(\d{1,3})", text)
    if not matches:
        return "Not found"
    licenses = {f"Series {num}" for _, num in matches}
    return ", ".join(sorted(licenses))

def extract_exam_filter(text):
    exams = re.findall(r"Series \d+", text)
    return ", ".join(sorted(set(exams))) if exams else "Not found"

def extract_address_parts(text):
    match = re.search(r"\d{3,5} .*?, ([A-Za-z\s]+), ([A-Z]{2})\s+(\d{5})", text)
    if match:
        city, state, zip_code = match.groups()
        return city.strip(), state.strip(), zip_code.strip()
    return "Not found", "Not found", "Not found"

def detect_inactive_status(text):
    return "Yes" if "Inactive - Continuing Education" in text else "No"

def detect_registration_type(text):
    broker = "Broker" if "BrokerCheck Report" in text else ""
    adviser = "Investment Adviser" if "Investment Adviser" in text or "IA" in text else ""
    if broker and adviser:
        return "Broker & Investment Adviser"
    elif broker:
        return "Broker"
    elif adviser:
        return "Investment Adviser"
    return "Not found"

async def fetch_and_parse(session, url):
    broker_id = url.split("/")[-1]
    pdf_url = f"https://files.brokercheck.finra.org/individual/individual_{broker_id}.pdf"

    try:
        async with session.get(pdf_url, timeout=20) as resp:
            if resp.status != 200:
                print(f"Failed to download PDF for {url} (status code {resp.status})")
                return None

            content = await resp.read()
            reader = PdfReader(io.BytesIO(content))
            full_text = " ".join([p.extract_text() or "" for p in reader.pages]).replace("\n", " ").strip()

            city, state, zip_code = extract_address_parts(full_text)

            return [
                broker_id,
                extract_field(full_text, "Name"),
                extract_field(full_text, "Address"),
                city,
                state,
                zip_code,
                extract_field(full_text, "Currently employed"),
                extract_field(full_text, "Previously employed"),
                extract_field(full_text, "Registered with this firm since"),
                extract_license_numbers(full_text),
                extract_exam_filter(full_text),
                extract_field(full_text, "Disclosure Count"),
                extract_field(full_text, "Disclosure Year"),
                detect_inactive_status(full_text),
                detect_registration_type(full_text),
                extract_exam_filter(full_text)
            ]
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

async def run_scraper():
    with open("missing_urls.txt", "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(HEADERS)

        connector = aiohttp.TCPConnector(limit_per_host=CONCURRENCY)
        async with aiohttp.ClientSession(connector=connector) as session:
            sem = asyncio.Semaphore(CONCURRENCY)
            progress = tqdm(total=len(urls), desc="Scraping Brokers")

            async def bound_fetch(url):
                async with sem:
                    result = await fetch_and_parse(session, url)
                    if result:
                        writer.writerow(result)
                    progress.update(1)

            await asyncio.gather(*[bound_fetch(url) for url in urls])

if __name__ == "__main__":
    asyncio.run(run_scraper())
