"""Fetch 10-K filings from SEC EDGAR for S&P 500 companies."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# SEC EDGAR requires a User-Agent header with contact info
HEADERS = {
    "User-Agent": "RAG-Demo contact@example.com",
    "Accept-Encoding": "gzip, deflate",
}

# Sample S&P 500 companies (CIK numbers)
# You can find CIK numbers at: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany
SAMPLE_COMPANIES = [
    {"ticker": "AAPL", "cik": "0000320193", "name": "Apple Inc."},
    {"ticker": "MSFT", "cik": "0000789019", "name": "Microsoft Corporation"},
    {"ticker": "GOOGL", "cik": "0001652044", "name": "Alphabet Inc."},
    {"ticker": "AMZN", "cik": "0001018724", "name": "Amazon.com Inc."},
    {"ticker": "JPM", "cik": "0000019617", "name": "JPMorgan Chase & Co."},
]


def get_10k_filings(cik: str, count: int = 1) -> list[dict]:
    """Get recent 10-K filing URLs for a company."""
    # SEC EDGAR API endpoint
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    filings = []
    recent = data.get("filings", {}).get("recent", {})
    
    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])
    
    for i, form in enumerate(forms):
        if form == "10-K" and len(filings) < count:
            accession = accession_numbers[i].replace("-", "")
            filings.append({
                "form": form,
                "accession_number": accession_numbers[i],
                "filing_date": filing_dates[i],
                "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_docs[i]}",
            })
    
    return filings


def extract_text_from_10k(url: str) -> str:
    """Download and extract text from a 10-K filing."""
    print(f"  Downloading: {url}")
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    # Parse HTML and extract text
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text
    text = soup.get_text(separator="\n")
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    
    return text


def fetch_sample_10k_filings(output_dir: str = "data_pipeline/10k_filings", num_companies: int = 3) -> list[dict]:
    """Fetch 10-K filings for sample companies."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    documents = []
    
    for company in SAMPLE_COMPANIES[:num_companies]:
        print(f"\nFetching 10-K for {company['name']} ({company['ticker']})...")
        
        try:
            filings = get_10k_filings(company["cik"], count=1)
            
            if not filings:
                print(f"  No 10-K filings found")
                continue
            
            filing = filings[0]
            text = extract_text_from_10k(filing["url"])
            
            # Save to file
            filename = f"{company['ticker']}_{filing['filing_date']}_10K.txt"
            filepath = output_path / filename
            filepath.write_text(text, encoding="utf-8")
            
            documents.append({
                "id": f"{company['ticker']}-10K-{filing['filing_date']}",
                "ticker": company["ticker"],
                "company": company["name"],
                "filing_date": filing["filing_date"],
                "text": text,
                "source": filing["url"],
                "filepath": str(filepath),
            })
            
            print(f"  Saved: {filename} ({len(text):,} chars)")
            
            # Be nice to SEC servers
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    # Save metadata
    metadata_path = output_path / "metadata.json"
    metadata = [
        {k: v for k, v in doc.items() if k != "text"}
        for doc in documents
    ]
    metadata_path.write_text(json.dumps(metadata, indent=2))
    print(f"\nSaved metadata to {metadata_path}")
    
    return documents


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch 10-K filings from SEC EDGAR")
    parser.add_argument("--output", default="data_pipeline/10k_filings", help="Output directory")
    parser.add_argument("--count", type=int, default=3, help="Number of companies to fetch")
    args = parser.parse_args()
    
    documents = fetch_sample_10k_filings(args.output, args.count)
    print(f"\nFetched {len(documents)} 10-K filings")
