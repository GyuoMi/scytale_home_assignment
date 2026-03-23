import os
import logging
import argparse

from extract import extract_prs_data
from transform import load_raw_data, process_pr_data, export_to_csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main(limit, start_date=None, end_date=None, author=None, label=None):
    logging.info("Starting the Scytale PR integration pipeline...") 

    # file paths
    raw_data_path = os.path.join("data", "raw_pr_data.json")
    report_path = os.path.join("data", "pr_report.csv")

    # Phase 1: Extract
    try:
        logging.info("--- Phase 1: Data Extraction ---")
        extract_prs_data(
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            author=author,
            label=label
        )
    except Exception as e:
        logging.error(f"Extraction phase failed: {e}")
        return # Halt execution if extraction fails

    # Phase 2: Transform
    try:
        logging.info("--- Phase 2: Data Transformation ---")
        raw_data = load_raw_data(raw_data_path)
        clean_data = process_pr_data(raw_data)
        export_to_csv(clean_data, report_path)
        logging.info("--- Pipeline completed successfully! ---")
    except Exception as e:
        logging.error(f"Transformation phase failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full PR data extraction and transformation pipeline.")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=10, 
        help="Limit the number of merged PRs to process (default: 10)"
    )
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format (e.g., 2024-01-01)")
    parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format (e.g., 2024-01-31)")
    parser.add_argument("--author", type=str, help="Filter PRs by GitHub username")
    parser.add_argument("--label", type=str, help="Filter PRs by label (e.g., 'bug')")
    args = parser.parse_args()
    
    main(
        limit=args.limit,
        start_date=args.start_date,
        end_date=args.end_date,
        author=args.author,
        label=args.label
    )