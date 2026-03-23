import os
import logging
import argparse

from extract import extract_prs_data
from transform import load_raw_data, process_pr_data, export_to_csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main(limit):
    logging.info("Starting the Scytale PR intergration pipeline...") 

    # file paths
    raw_data_path = os.path.join("data", "raw_pr_data.json")
    report_path = os.path.join("data", "pr_report.csv")

    # Phase 1: Extract
    try:
        logging.info("--- Phase 1: Data Extraction ---")
        extract_prs_data(limit=limit)
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
    args = parser.parse_args()
    
    main(limit=args.limit)