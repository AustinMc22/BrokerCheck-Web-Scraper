import os
import csv
import re
from PyPDF2 import PdfReader

PDF_FOLDER = "sample_brokers"
OUTPUT_FILE = "cleaned_sample_output.csv"

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

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    return " ".join([page.extract_text() or "" for page in reader.pages]).replace("\n", " ").strip()

def extract_crd_from_filename(filename):
    match = re.search(r"(\d+)", filename)
    return match.group(1) if match else "Not found"

def extract_name(text):
    # Normalize the text to collapse whitespace
    text = re.sub(r"\s+", " ", text)

    # Look for "<First> <Middle/Initial> <Last> CRD#"
    match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+))\s+CRD#", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        return name.title()  # Make sure it looks like "John A. Smith"
    return "Not found"

    # Strategy 2: Fallback to "[NAME] CRD# 123456" from page header
    match = re.search(r"([A-Z][A-Z\s\.\-']+?)\s+CRD#\s+\d{6,}", text)
    if match:
        name = match.group(1).strip()
        return name

    return "Not found"

def extract_address(text):
    import re

    # Return "Not a Broker" if the person is only an Investment Adviser
    if "This broker is not currently registered." in text:
        return "Not a Broker", "Not a Broker", "Not a Broker"

    # Common street-type words to exclude
    bad_street_words = {"rd", "road", "ave", "avenue", "blvd", "drive", "dr", "plaza", "st", "ste", "suite", "place"}

    lines = text.splitlines()

    for line in lines:
        match = re.search(r"([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5})", line)
        if match:
            raw_location, state, zip_code = match.groups()

            # Split into words and filter out known street words
            words = raw_location.strip().split()
            filtered = []

            for word in reversed(words):
                if word.lower() in bad_street_words or len(word) == 1:
                    break
                filtered.insert(0, word)

            city = " ".join(filtered)
            return city.title(), state.upper(), zip_code.strip()

    return "Not found", "Not found", "Not found"


def extract_current_firm(text):
    import re

    # Handle Investment Adviser–only cases
    if "This broker is not currently registered." in text:
        return "Not a Broker"

    match = re.search(
        r"Currently employed by and registered with the following Firm\(s\):(.*?)Registered with this firm since:",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        firm_block = match.group(1).strip()
        first_line = firm_block.splitlines()[0].strip()

        # Regex to cut off after common firm suffixes
        suffix_pattern = r"^(.*?\b(?:LLC|L\.L\.C\.|Limited Liability Company|Inc\.?|Incorporated|Corp\.?|Corporation|Co\.?|Company|Ltd\.?|Limited))\b"
        suffix_match = re.search(suffix_pattern, first_line, re.IGNORECASE)

        if suffix_match:
            return suffix_match.group(1).strip()

        return first_line

    return "Not found"

def extract_previous_firms(text):
    import re

    match = re.search(r"This broker was previously registered with the following securities firm\(s\):(.*?)Employment History", text, re.DOTALL)
    if not match:
        return "Not found"

    block = match.group(1)

    # Extract firm names that may be preceded by IA or B
    firm_matches = re.findall(r"(?:IA\s+|B\s+)?([A-Z][A-Z &.,'\-]+?)\s+CRD#", block)

    # Clean and deduplicate
    clean_firms = list(dict.fromkeys([firm.strip().title() for firm in firm_matches]))
    return ", ".join(clean_firms) if clean_firms else "Not found"

def extract_first_registration_year(text):
    import re

    # 1. Search "previous firms" section
    prev_match = re.search(
        r"This broker was previously registered with the following securities firm\(s\):(.*?)Employment History",
        text,
        re.DOTALL | re.IGNORECASE
    )

    previous_years = []
    if prev_match:
        previous_block = prev_match.group(1)
        previous_years = re.findall(r"\b(19[5-9]\d|20[0-4]\d)\b", previous_block)

    # 2. If none found, look in "current firm" section
    if not previous_years:
        current_match = re.search(
            r"Currently employed by and registered with the following Firm\(s\):(.*?)Registered with this firm since:",
            text,
            re.DOTALL | re.IGNORECASE
        )
        if current_match:
            current_block = current_match.group(1)
            current_years = re.findall(r"\b(19[5-9]\d|20[0-4]\d)\b", current_block)
            previous_years = current_years  # fallback

    # 3. Return the earliest year found
    if previous_years:
        oldest_year = min(int(y) for y in previous_years)
        return str(oldest_year)

    return "Not found"

def extract_licenses(text):
    # Match Series exams with or without TO (e.g., Series 6, Series 52TO, Series 79TO)
    licenses = re.findall(r"Series \d{1,2}(?:TO)?", text)

    # Check for SIE or SIE TO
    if "Securities Industry Essentials Examination" in text:
        licenses.append("SIE")

    # Remove duplicates and sort
    unique = sorted(set(licenses), key=lambda x: (x != "SIE", x))

    return ", ".join(unique) if unique else "Not found"

def extract_disclosures(text):
    if "Disclosure Event Details" in text or "disclosures have been reported" in text.lower():
        return "Yes"
    if "No disclosures reported for this broker" in text or "no disclosure" in text.lower():
        return "No"
    return "Not found"

def extract_registration_type(text):
    import re

    # Step 1: If the person is not currently registered with a broker-dealer
    if "Currently employed by and registered with the following Firm(s):" not in text:
        return "Investment Adviser"

    # Step 2: Search for the capitalized phrase in the Registrations table
    # This table comes *after* the current firm section, so we only scan after that
    current_section = re.search(
        r"Currently employed by and registered with the following Firm\(s\):", text
    )
    if current_section:
        registration_table_start = current_section.end()
        rest_of_text = text[registration_table_start:]

        # Look for exact capitalization "Investment Adviser Representative"
        if "Investment Adviser Representative" in rest_of_text:
            return "Broker & Investment Adviser"
        else:
            return "Broker"

    return "Not found"

def process_pdf(filename):
    filepath = os.path.join(PDF_FOLDER, filename)
    text = extract_text_from_pdf(filepath)
    crd_number = os.path.splitext(filename)[0].replace("individual_", "")
    url = f'"https://brokercheck.finra.org/individual/summary/{crd_number}"'
    full_name = extract_name(text)
    current_firm = extract_current_firm(text)
    city, state, zip_code = extract_address(text)
    previous_firms = extract_previous_firms(text)
    registration_year = extract_first_registration_year(text)
    licenses = extract_licenses(text)
    disclosures = extract_disclosures(text)
    reg_type = extract_registration_type(text)

    return [
        url,
        crd_number,
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

def main():
    files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        for file in files:
            row = process_pdf(file)
            writer.writerow(row)
    print(f"✅ Extracted {len(files)} broker profiles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
