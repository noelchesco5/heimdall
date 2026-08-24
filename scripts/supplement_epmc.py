"""Probe + harvest captioned dermatology figures from Europe PMC.

Europe PMC exposes open-access article figures with captions. We search
for skin-condition terms, pull figure captions, and download the figure
images, appending them to the corpus.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGS = DATA / "figures"

QUERIES = {
    "skin rash clinical photograph dermatology": "rash",
    "bullous blister vesicular skin lesions photograph": "blister",
    "erythema skin eruption dermatology figure": "eruption",
    "burn injury skin photograph": "burn",
}

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def search(query, page_size=12):
    url = API + "?" + urllib.parse.urlencode({
        "query": f"({query}) AND OPEN_ACCESS:Y AND SRC:MED",
        "format": "json",
        "pageSize": page_size,
        "resultType": "core",
    })
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def main():
    probe_only = "--probe" in sys.argv
    total = 0
    for query, slug in QUERIES.items():
        try:
            d = search(query)
        except Exception as exc:
            print(f"{slug}: search failed {exc}")
            continue
        print(f"{slug}: {d['hitCount']} open-access hits")
        if probe_only:
            for r in d["resultList"]["result"][:2]:
                print("   ", r.get("pmcid"), "|", (r.get("title") or "")[:60])
            continue
    return total


if __name__ == "__main__":
    main()
