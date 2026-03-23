# Scytale Junior Data Engineer Home Assignment

This repository contains a robust data extraction and transformation pipeline that integrates with the GitHub API. The application is designed to fetch merged pull requests (PRs) from the `home-assistant/core` repository and evaluate whether each PR passed its code review and its required status checks before being merged.

## Project Structure

The project is broken down into modular components to ensure separation of concerns and maintainability:

* `extract.py`: Responsible for authenticating with GitHub, dynamically constructing Search API queries, handling API pagination, and downloading raw PR, review, and check-run data into a JSON format.
* `transform.py`: Parses the raw JSON, applies business logic to determine `CR_Passed` and `CHECKS_PASSED`, and exports the final dataset.
* `main.py`: The central orchestrator that runs the extraction and transformation phases sequentially and handles CLI arguments.
* `data/`: The output directory where `raw_pr_data.json` and the final `pr_report.csv` are stored (contents ignored by git).
* `.env`: Stores the sensitive Personal Access Token (ignored via `.gitignore`).

## Prerequisites and Setup

1.  **Environment Setup:** Ensure you have Python 3 installed.
2.  **Install Dependencies:** Run the following command to install the required libraries:
    ```bash
    pip install requests python-dotenv
    ```

### Authentication Method

This project uses a GitHub Personal Access Token (PAT) for authentication to avoid strict rate limits and ensure secure access. 

**Setup Instructions:**
1. Generate a **Fine-grained Personal Access Token** in your GitHub Developer Settings.
2. Grant the token **Public Repositories (read-only)** access.
3. In the root directory of this project, create a file named `.env`.
4. Add your token to the file like so:
    ```text
    GITHUB_PAT="your_fine_grained_token_here"
    ```
*Note: The `.env` file is intentionally excluded from version control via `.gitignore` to prevent credential leaks.*

## GitHub API Endpoints Used

The extraction script leverages the following GitHub REST API endpoints (API Version: 2022-11-28):

1.  **Search Issues/PRs:** `GET /search/issues`
    * Used to perform highly efficient, server-side filtering of merged pull requests based on date, author, and labels.
2.  **Pull Requests:** `GET /repos/{owner}/{repo}/pulls/{pull_number}`
    * Used to fetch the full PR object to extract the `head_sha` commit reference.
3.  **Reviews:** `GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews`
    * Used to retrieve the review history for a specific PR to check for an `APPROVED` state.
4.  **Check Runs:** `GET /repos/{owner}/{repo}/commits/{ref}/check-runs`
    * Used to retrieve the status checks for the specific commit associated with the PR to ensure all required checks resulted in a `success`, `neutral`, or `skipped` conclusion.

## How to Run the Pipeline

You can run the entire pipeline using the orchestrator script. To prevent exhausting API rate limits during testing, you can use the command-line interface (CLI) to filter your data payload.

### Available CLI Command Options
The `main.py` script accepts the following optional arguments to filter results:
* `--limit`: Limit the maximum number of merged PRs to process (Default: `10`).
* `--start-date`: Filter for PRs merged on or after this date (Format: `YYYY-MM-DD`).
* `--end-date`: Filter for PRs merged on or before this date (Format: `YYYY-MM-DD`).
* `--author`: Filter for PRs submitted by a specific GitHub username.
* `--label`: Filter for PRs containing a specific label (e.g., `"bug"`).

### Usage Examples
```bash
# Basic run with the default limit (10 PRs)
python main.py

# Filter by a specific date range with a custom limit
python main.py --limit 5 --start-date 2024-01-01 --end-date 2024-02-28

# Combine multiple filters (Author and Label)
python main.py --limit 15 --author "bdraco" --label "bugfix"