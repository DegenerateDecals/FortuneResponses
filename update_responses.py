import requests
import base64
import time
import os
import json  # Add this import to handle JSON serialization

# Load sensitive information from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "YourGitHubUsername")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "YourRepoName")
FILE_PATH = os.environ.get("FILE_PATH", "responses.json")


def encode_content(content):
    """
    Encode file content in base64 for GitHub API.
    """
    return base64.b64encode(content.encode("utf-8")).decode("utf-8")


def handle_rate_limit(headers):
    """
    Handle GitHub API rate limits.
    """
    reset_time = int(headers.get("X-RateLimit-Reset", 0))
    wait_time = reset_time - int(time.time())
    if wait_time > 0:
        print(f"Rate limit exceeded. Retrying after {wait_time} seconds...")
        time.sleep(wait_time)
        return True
    return False


def update_github_file(new_content):
    """
    Create or update responses.json in your GitHub repo with 'new_content' (string).
    Uses token-based Auth with your GitHub username + personal token.
    """
    # Prepare the authorization header
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # GitHub API endpoint for the file
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"

    try:
        # Step 1: Fetch the current file information (to get the SHA)
        print("Fetching file information from GitHub...")
        get_resp = requests.get(url, headers=headers)

        if get_resp.status_code == 200:
            # File exists, retrieve SHA
            response_json = get_resp.json()
            current_sha = response_json.get("sha", None)
            if not current_sha:
                print("Error: Unable to retrieve file SHA.")
                return
            print(f"File exists. Current SHA: {current_sha}")

            # Prepare payload to update the existing file
            payload = {
                "message": "Update fortune response",
                "content": encode_content(new_content),
                "sha": current_sha
            }
        elif get_resp.status_code == 404:
            # File does not exist; create a new one
            print("File does not exist. Creating a new file.")
            payload = {
                "message": "Create fortune response",
                "content": encode_content(new_content)
            }
        elif get_resp.status_code == 403 and "X-RateLimit-Remaining" in get_resp.headers:
            # Handle rate-limiting on GET
            if handle_rate_limit(get_resp.headers):
                update_github_file(new_content)  # Retry after waiting
            else:
                print("Rate limit exceeded. Please try again later.")
            return
        else:
            # Handle other unexpected GET errors
            print(f"Error fetching file info: {get_resp.status_code} - {get_resp.text}")
            return

        # Step 2: PUT request to update or create the file
        print("Attempting to update/create the file on GitHub...")
        put_resp = requests.put(url, headers=headers, json=payload)

        if put_resp.status_code in (200, 201):
            print("File successfully created/updated on GitHub!")
        elif put_resp.status_code == 403 and "X-RateLimit-Remaining" in put_resp.headers:
            # Handle rate-limiting on PUT
            if handle_rate_limit(put_resp.headers):
                update_github_file(new_content)  # Retry after waiting
            else:
                print("Rate limit exceeded. Please try again later.")
        else:
            print(f"Error updating/creating file: {put_resp.status_code} - {put_resp.text}")

    except requests.exceptions.RequestException as e:
        print(f"Exception during GitHub API call: {e}")


# Example usage
if __name__ == "__main__":
    # Replace this with your new JSON content
    new_json_data = {
        "fortune": "This is an example fortune message."
    }

    # Update the file on GitHub
    update_github_file(json.dumps(new_json_data, indent=2))
