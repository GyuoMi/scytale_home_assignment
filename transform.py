import os
import json
import csv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_raw_data(filepath):
    if not os.path.exists(filepath):
        logging.error(f"Recheck if JSON data file is at {filepath}. Run extract.py again")
        raise FileNotFoundError(f"Missing {filepath}")


    with open(filepath, "r", encoding="utf-8") as f:
        logging.info(f"Loading raw pr data from {filepath}")
        return json.load(f)

def process_pr_data(raw_data):
    # transforms the raw PR json into a tabular format
    # also calculates passing conditions for the CRs and checks

    logging.info(f"Analysing data for {len(raw_data)} pull requests...")
    transformed_records = []

    for item in raw_data:
        pr = item.get("pr_info", {})
        reviews = item.get("reviews", [])
        checks = item.get("checks", [])

        # 1. Extract basic metadata
        pr_number = pr.get("number")
        pr_title = pr.get("title")
        author = pr.get("user", {}).get("login")
        merge_date = pr.get("merged_at")

        # 2. Compute CR_Passed (At least one APPROVED review)
        # We use a generator expression inside any() for efficiency (can be large/infinite)
        # https://stackoverflow.com/a/47792
        cr_passed = any(review.get("state") == "APPROVED" for review in reviews)

        # 3. Compute CHECKS_PASSED (All required checks passed before merge)
        # Valid successful conclusions from the GitHub API
        passing_conclusions = {"success", "neutral", "skipped"}
        
        if not checks:
            # If there are no checks run, we can technically assume nothing failed.
            checks_passed = True
        else:
            checks_passed = all(
                check.get("status") == "completed" and check.get("conclusion") in passing_conclusions
                for check in checks
            )

        # Append the cleaned record
        transformed_records.append({
            "PR_Number": pr_number,
            "PR_Title": pr_title,
            "Author": author,
            "Merge_Date": merge_date,
            "CR_Passed": cr_passed,
            "CHECKS_PASSED": checks_passed
        })

    return transformed_records    

def export_to_csv(data, output_path):
    """Writes the transformed data to a CSV file."""
    if not data:
        logging.warning("No data to export.")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ["PR_Number", "PR_Title", "Author", "Merge_Date", "CR_Passed", "CHECKS_PASSED"]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(data)
        
    logging.info(f"Successfully exported {len(data)} records to {output_path}")

if __name__ == "__main__":
    input_file = os.path.join("data", "raw_pr_data.json")
    output_file = os.path.join("data", "pr_report.csv")
    
    try:
        raw_data = load_raw_data(input_file)
        clean_data = process_pr_data(raw_data)
        export_to_csv(clean_data, output_file)
    except Exception as e:
        logging.error(f"Transformation failed: {e}")