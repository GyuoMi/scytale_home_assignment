import os
import json
import logging
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
    """Fetches all pages for standard GitHub API list requests."""
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

def extract_prs_data(limit=10, start_date=None, end_date=None, author=None, label=None):    
    """
    Fetches merged PRs using the highly efficient GitHub Search API,
    then retrieves their associated reviews and checks.
    Also paginates if filtered results go to the next page(s)
    """
    logging.info(f"Constructing search query for {ORG}/{REPO}...")
    
    # 1. Build the GitHub Search API query
    query_parts = [f"repo:{ORG}/{REPO}", "is:pr", "is:merged"]
    
    if start_date and end_date:
        query_parts.append(f"merged:{start_date}..{end_date}")
    elif start_date:
        query_parts.append(f"merged:>={start_date}")
    elif end_date:
        query_parts.append(f"merged:<={end_date}")
        
    if author:
        query_parts.append(f"author:{author}")
        
    if label:
        # Wrap label in quotes to handle spaces
        query_parts.append(f'label:"{label}"')

    query_string = " ".join(query_parts)
    logging.info(f"Executing Search API query: {query_string}")

    search_url = f"{BASE_URL}/search/issues"
    # Cap per_page at 100 as per GitHub API strict limits
    search_params = {"q": query_string, "per_page": min(limit, 100)}

    search_results = []
    current_url = search_url
    current_params = search_params

    # 2. Execute the Search with Pagination
    while current_url and len(search_results) < limit:
        response = requests.get(current_url, headers=HEADERS, params=current_params)
        response.raise_for_status()
        
        page_items = response.json().get("items", [])
        search_results.extend(page_items)
        
        # Trim if we slightly overshot the limit on the final page
        if len(search_results) >= limit:
            search_results = search_results[:limit]
            break
            
        # Get the next page URL
        current_url = response.links.get('next', {}).get('url')
        current_params = None

    logging.info(f"Search returned {len(search_results)} matching PRs. Fetching details...")

    extracted_data = []

    # 3. Fetch detailed PR info, reviews, and checks
    for item in search_results:
        pr_number = item["number"]
        
        logging.info(f"Fetching full details, reviews, and checks for PR #{pr_number}...")

        # The Search API returns 'Issue' objects which lack the head commit SHA.
        # We must fetch the full PR object directly to get the SHA for the checks endpoint.
        pr_url = f"{BASE_URL}/repos/{ORG}/{REPO}/pulls/{pr_number}"
        pr_response = requests.get(pr_url, headers=HEADERS)
        pr_response.raise_for_status()
        pr = pr_response.json()
        
        head_sha = pr["head"]["sha"]

        # Fetch Reviews
        reviews_url = f"{BASE_URL}/repos/{ORG}/{REPO}/pulls/{pr_number}/reviews"
        reviews = fetch_paginated_data(reviews_url)

        # Fetch Checks
        checks_url = f"{BASE_URL}/repos/{ORG}/{REPO}/commits/{head_sha}/check-runs"
        checks_params = {"per_page": 100}
        checks_response = requests.get(checks_url, headers=HEADERS, params=checks_params)
        
        if checks_response.status_code == 200:
            checks = checks_response.json().get("check_runs", [])
        else:
            logging.warning(f"Could not fetch checks for PR #{pr_number}")
            checks = []

        # Compile the raw data payload
        extracted_data.append({
            "pr_info": pr,
            "reviews": reviews,
            "checks": checks
        })

    # Save the output
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_pr_data.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4)
        
    logging.info(f"Successfully extracted raw data to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract raw PR data from GitHub.")
    parser.add_argument("--limit", type=int, default=10, help="Limit PRs to fetch")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format")
    parser.add_argument("--author", type=str, help="Filter PRs by GitHub username")
    parser.add_argument("--label", type=str, help="Filter PRs by label (e.g., 'bug')")
    args = parser.parse_args()
    
    extract_prs_data(
        limit=args.limit, 
        start_date=args.start_date, 
        end_date=args.end_date,
        author=args.author,
        label=args.label
    )