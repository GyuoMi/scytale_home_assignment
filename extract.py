import os
import logging
import json
import argparse
import requests

from dotenv import load_dotenv

load_dotenv()

GITHUB_PAT = os.getenv("GITHUB_PAT")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_PAT}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
    }

BASE_URL = "https://api.github.com"
ORG = "home-assistant"
REPO = "core"

def fetch_paginated_data(url, params=None):
    # Fetches all pages per github API requests

    results = []
    current_url = url
    current_params = params

    while current_url:
        response = requests.get(current_url, headers=HEADERS, params=current_params)
        response.raise_for_status()
        results.extend(response.json())

        current_url = response.links.get('next', {}).get('url')
        current_params = None

    return results

def extract_prs_data(limit=10):
    # fetch merged PRs from target repo, along with their associated reviews and checks
    # limit=10 so dont get rate limited while testing (also works as a way to filter results)
    logging.info(f"Fetching closed PRs from {ORG}/{REPO}...")
    
    # GitHub does not have a "merged" state filter, so we fetch "closed" PRs
    # and filter them locally. We sort by updated to get the most recent ones.
    prs_url = f"{BASE_URL}/repos/{ORG}/{REPO}/pulls"
    pr_params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100}
    
    # We only fetch the first page of closed PRs initially to find our merged ones, 
    # to avoid pulling thousands of records unnecessarily.
    response = requests.get(prs_url, headers=HEADERS, params=pr_params)
    response.raise_for_status()
    all_closed_prs = response.json()
    
    # Filter for merged PRs only
    merged_prs = [pr for pr in all_closed_prs if pr.get("merged_at")]
    
    # Apply the limit (default 10) so we don't exhaust the API rate limit during development
    merged_prs = merged_prs[:limit]
    logging.info(f"Processing {len(merged_prs)} merged PRs...")

    extracted_data = []

    for pr in merged_prs:
        pr_number = pr["number"]
        head_sha = pr["head"]["sha"]
        
        logging.info(f"Fetching reviews and checks for PR #{pr_number}...")

        # 1. Fetch Reviews for the PR
        reviews_url = f"{BASE_URL}/repos/{ORG}/{REPO}/pulls/{pr_number}/reviews"
        reviews = fetch_paginated_data(reviews_url)

        # 2. Fetch Status Check Runs for the specific commit SHA
        # The check-runs endpoint returns a dict, not a list, so we handle it directly
        checks_url = f"{BASE_URL}/repos/{ORG}/{REPO}/commits/{head_sha}/check-runs"
        checks_params = {"per_page": 100}
        checks_response = requests.get(checks_url, headers=HEADERS, params=checks_params)
        
        if checks_response.status_code == 200:
            checks = checks_response.json().get("check_runs", [])
        else:
            logging.warning(f"Could not fetch checks for PR #{pr_number}")
            checks = []

        # Compile the raw data payload for this specific PR
        extracted_data.append({
            "pr_info": pr,
            "reviews": reviews,
            "checks": checks
        })

    # Ensure the data directory exists and save the output
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_pr_data.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4)
        
    logging.info(f"Successfully extracted raw data to {output_path}")

if __name__ == "__main__":
    # Command-line argument to control the volume of data fetched
    parser = argparse.ArgumentParser(description="Extract raw PR data from GitHub.")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=10, 
        help="Limit the number of merged PRs to fetch (default: 10)"
    )
    args = parser.parse_args()
    
    extract_prs_data(limit=args.limit)