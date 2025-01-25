import requests
import json
import base64
from typing import Optional, List

# ─────────────────────────────────────────────────────────────────────────────
#  Groq API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"

# ─────────────────────────────────────────────────────────────────────────────
#  GITHUB CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_USERNAME = "DegenerateDecals"
GITHUB_TOKEN = "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"
GITHUB_REPO = "FortuneResponses"
FILE_PATH = "responses.json"

# ─────────────────────────────────────────────────────────────────────────────
#  Preflight Check for GitHub Token
# ─────────────────────────────────────────────────────────────────────────────
def verify_github_token() -> bool:
    """
    Test the GitHub token against the GitHub API to ensure it is valid.
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            print("GitHub token is valid.")
            return True
        elif response.status_code == 401:
            print("Error: Unauthorized. Check your GitHub token.")
            return False
        else:
            print(f"Unexpected error: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error verifying GitHub token: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
#  Query Groq for a New Fortune
# ─────────────────────────────────────────────────────────────────────────────
def query_groq(name: str, keywords: List[str]) -> str:
    """
    Generate a fortune from the Groq API using the provided 'name' and 'keywords'.
    Returns the fortune text directly or an error string if something fails.
    """
    prompt = f"Generate a fortune for {name} based on these keywords: {', '.join(keywords)}."
    payload = {
        "model": "llama-3.2-1b-preview",
        "messages": [
            {"role": "system", "content": "You are a fortune teller."},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            return "Error: Groq API returned an unexpected format."
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Groq: {e}"
    except ValueError as e:
        return f"Error parsing response from Groq: {e}"

# ─────────────────────────────────────────────────────────────────────────────
#  Update or Create responses.json on GitHub via REST API
# ─────────────────────────────────────────────────────────────────────────────
def update_github_file(new_content: str) -> None:
    """
    Create or update responses.json in your GitHub repo with 'new_content' (string).
    Uses token-based Auth with your GitHub username + personal token.
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"

    try:
        # Check if the file exists to obtain the current SHA
        get_resp = requests.get(url, headers=headers)
        if get_resp.status_code == 401:
            print("Error: Unauthorized. Check your GitHub token or permissions.")
            return
        get_resp.raise_for_status()

        if get_resp.status_code == 200:
            # File exists, extract the current SHA
            current_sha = get_resp.json().get("sha")
            if not current_sha:
                print("Error: Unable to retrieve file SHA from GitHub response.")
                return
            payload = {
                "message": "Update fortune response",
                "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
                "sha": current_sha
            }
        elif get_resp.status_code == 404:
            # File does not exist -> create it
            payload = {
                "message": "Create fortune response",
                "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            }
        else:
            print(f"Error fetching file info: {get_resp.status_code} - {get_resp.text}")
            return

        # PUT request to create or update the file
        put_resp = requests.put(url, headers=headers, json=payload)
        if put_resp.status_code == 401:
            print("Error: Unauthorized. Check your GitHub token or permissions.")
            return
        put_resp.raise_for_status()

        if put_resp.status_code in (200, 201):
            print("File successfully created/updated on GitHub!")
        else:
            print(f"Unexpected status code from GitHub: {put_resp.status_code} - {put_resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with GitHub: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  Main Execution Flow
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Verify GitHub token before proceeding
    if not verify_github_token():
        print("Aborting script due to invalid GitHub token.")
        exit(1)

    # Example usage
    name = "Player123"
    keywords = ["success", "happiness", "adventure"]

    # A) Generate a fortune
    fortune_text = query_groq(name, keywords)
    print(f"Generated fortune: {fortune_text}")

    # B) Prepare JSON for responses.json
    new_json_data = {
        "fortune": fortune_text
    }

    # C) Update or create the file on GitHub
    update_github_file(json.dumps(new_json_data, indent=2))

    # D) Done
    print("Fortune process complete!")
