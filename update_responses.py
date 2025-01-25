import requests
import json
import base64
import os

# ─────────────────────────────────────────────────────────────────────────────
#  Groq API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"  # Replace with your valid Groq key

# ─────────────────────────────────────────────────────────────────────────────
#  GITHUB CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_USERNAME = "DegenerateDecals"  # Replace if needed
GITHUB_TOKEN = "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"  # Replace with your valid GitHub PAT
GITHUB_REPO = "FortuneResponses"
FILE_PATH = "responses.json"

# ─────────────────────────────────────────────────────────────────────────────
#  1) Query Groq for a New Fortune
# ─────────────────────────────────────────────────────────────────────────────
def query_groq(name, keywords):
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
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Groq: {e}"

    if response.status_code == 200:
        # Expecting an OpenAI-style response with choices/message/content
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            return "Error: Groq API returned an unexpected format."
    else:
        return f"Error from Groq API: {response.status_code} - {response.text}"

# ─────────────────────────────────────────────────────────────────────────────
#  2) Update or Create responses.json on GitHub via REST API
# ─────────────────────────────────────────────────────────────────────────────
def update_github_file(new_content):
    """
    Create or update responses.json in your GitHub repo with 'new_content' (string).
    Uses the token-based Auth with your GitHub username + personal token.
    """
    # Prepare the authorization header
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # The endpoint for the specific file in your repo
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"

    # 1) Attempt to get the current file's SHA
    get_resp = requests.get(url, headers=headers)
    
    if get_resp.status_code == 200:
        # File exists, extract the current SHA
        current_sha = get_resp.json()["sha"]

        # Prepare payload to update existing file
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
        # Some other error
        print(f"Error fetching file info: {get_resp.status_code} - {get_resp.text}")
        return

    # 2) PUT request to update or create the file
    put_resp = requests.put(url, headers=headers, json=payload)
    if put_resp.status_code in (200, 201):
        print("File successfully created/updated on GitHub!")
    else:
        print(f"Error updating/creating file: {put_resp.status_code} - {put_resp.text}")

# ─────────────────────────────────────────────────────────────────────────────
#  3) Main Execution Flow
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Example usage
    name = "Player123"
    keywords = ["success", "happiness", "adventure"]

    # A) Generate a fortune
    fortune_text = query_groq(name, keywords)
    print(f"Generated fortune: {fortune_text}")

    # B) Prepare JSON for responses.json
    #    (Extend this structure as needed.)
    new_json_data = {
        "fortune": fortune_text
    }

    # C) Update or create the file on GitHub
    update_github_file(json.dumps(new_json_data, indent=2))

    # D) Done
    print("Fortune process complete!")
