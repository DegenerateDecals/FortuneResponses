import requests
import json
import base64

# Groq API Configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"

# GitHub Configuration
GITHUB_REPO = "your_username/FortuneResponses"  # Replace "your_username" with your GitHub username
GITHUB_TOKEN = "your_github_personal_access_token"  # Replace with your GitHub personal access token
RAW_FILE_PATH = "responses.json"  # File to update in GitHub

def query_groq(user_message):
    """Send a request to the Groq API."""
    payload = {
        "model": "llama-3.2-1b-preview",
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    return response.json()

def push_to_github(content):
    """Update the responses.json file in the GitHub repository."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{RAW_FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    # Fetch the existing file's SHA (needed for updates)
    response = requests.get(url, headers=headers)
    sha = response.json().get("sha", "")
    # Prepare the payload
    payload = {
        "message": "Update fortune response",
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha,
    }
    requests.put(url, headers=headers, json=payload)

if __name__ == "__main__":
    user_message = "Tell me a fortune about success and happiness."
    groq_response = query_groq(user_message)
    push_to_github(json.dumps(groq_response))
